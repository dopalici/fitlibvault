import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import { fileURLToPath } from "url";
import { initializeApp, cert } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";
import Stripe from "stripe";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize Firebase Admin
let admin;
try {
  admin = initializeApp({
    credential: cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY || "{}")),
  });
} catch (error) {
  console.warn("Firebase Admin not initialized - service account key missing");
}

const db = admin ? getFirestore(admin) : null;

// Initialize Stripe with error handling
let stripe: Stripe | null = null;
try {
  if (process.env.STRIPE_SECRET_KEY) {
    stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
      apiVersion: "2026-04-22.dahlia",
    });
  } else {
    console.warn("Stripe not initialized - STRIPE_SECRET_KEY missing");
  }
} catch (error) {
  console.warn("Stripe initialization failed:", error);
}

async function startServer() {
  const app = express();
  const PORT = parseInt(process.env.PORT || "3000");

  app.use(cors());

  // Stripe webhook must read raw body before JSON middleware.
  app.post('/api/stripe/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
    if (!stripe) {
      return res.status(503).json({ error: "Stripe not configured" });
    }

    const sig = req.headers['stripe-signature'] as string;
    const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

    let event;
    try {
      event = stripe.webhooks.constructEvent(req.body, sig, endpointSecret || "");
    } catch (err: any) {
      console.log('Webhook signature verification failed.', err?.message);
      return res.status(400).send(`Webhook Error: ${err?.message}`);
    }

    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        if (db && session.metadata?.userId) {
          await db.collection('users').doc(session.metadata.userId).set({
            subscriptionStatus: 'active',
            subscriptionId: String(session.subscription || ''),
            premium: true,
            updatedAt: new Date()
          }, { merge: true });
        }
        break;
      }
      case 'customer.subscription.deleted':
      case 'customer.subscription.paused': {
        const subscription = event.data.object as Stripe.Subscription;
        if (db) {
          const users = await db
            .collection('users')
            .where('subscriptionId', '==', subscription.id)
            .limit(1)
            .get();
          if (!users.empty) {
            await users.docs[0].ref.set(
              {
                subscriptionStatus: 'inactive',
                premium: false,
                updatedAt: new Date()
              },
              { merge: true }
            );
          }
        }
        break;
      }
      default:
        break;
    }

    res.json({ received: true });
  });

  app.use(express.json());

  // API routes
  app.get("/api/health", (req, res) => {
    res.json({ 
      status: "ok", 
      message: "FitLib API is running",
      firestore: db ? "connected" : "not connected",
      timestamp: new Date().toISOString()
    });
  });

  // Nodes API - Get all nodes with optional filtering
  app.get("/api/nodes", async (req, res) => {
    try {
      if (!db) {
        return res.status(503).json({ error: "Database not available" });
      }

      const { category, series, limit = 50, search } = req.query;
      let queryRef: any = db.collection("nodes");
      const searchTerm = typeof search === "string" ? search.trim() : "";

      if (category) {
        queryRef = queryRef.where("category", "==", category);
      }

      if (series) {
        queryRef = queryRef.where("series", "==", series);
      }

      const snapshot = await queryRef.limit(parseInt(limit as string)).get();
      const nodes = snapshot.docs
        .map((doc: any) => ({ id: doc.id, ...doc.data() }))
        .filter((node: any) => {
          if (!searchTerm) return true;
          const normalized = searchTerm.toLowerCase();
          const title = String(node.title || "").toLowerCase();
          const content = String(node.content || "").toLowerCase();
          const tags = Array.isArray(node.tags) ? node.tags.join(" ").toLowerCase() : "";
          return (
            title.includes(normalized) ||
            content.includes(normalized) ||
            tags.includes(normalized)
          );
        });

      res.json({ nodes, count: nodes.length });
    } catch (error) {
      console.error("Error fetching nodes:", error);
      res.status(500).json({ error: "Failed to fetch nodes" });
    }
  });

  // Get single node by ID
  app.get("/api/nodes/:id", async (req, res) => {
    try {
      if (!db) {
        return res.status(503).json({ error: "Database not available" });
      }

      const nodeRef = db.collection("nodes").doc(req.params.id);
      const [nodeDoc, citationsSnapshot] = await Promise.all([
        nodeRef.get(),
        nodeRef.collection("citations").get()
      ]);
      
      if (!nodeDoc.exists) {
        return res.status(404).json({ error: "Node not found" });
      }

      const citations = citationsSnapshot.docs.map((citationDoc: any) => ({
        id: citationDoc.id,
        ...citationDoc.data()
      }));
      res.json({ id: nodeDoc.id, ...nodeDoc.data(), citations });
    } catch (error) {
      console.error("Error fetching node:", error);
      res.status(500).json({ error: "Failed to fetch node" });
    }
  });

  // User progress tracking
  app.get("/api/users/:userId/progress", async (req, res) => {
    try {
      if (!db) {
        return res.status(503).json({ error: "Database not available" });
      }

      const userProgressRef = db.collection("userProgress").doc(req.params.userId);
      const doc = await userProgressRef.get();

      if (!doc.exists) {
        return res.json({ 
          completedNodes: [],
          favorites: [],
          studyStreak: 0,
          totalReadingTime: 0
        });
      }

      res.json(doc.data());
    } catch (error) {
      console.error("Error fetching user progress:", error);
      res.status(500).json({ error: "Failed to fetch progress" });
    }
  });

  // Update user progress
  app.post("/api/users/:userId/progress", async (req, res) => {
    try {
      if (!db) {
        return res.status(503).json({ error: "Database not available" });
      }

      const { nodeId, action, readingTime } = req.body;
      const userProgressRef = db.collection("userProgress").doc(req.params.userId);

      await db.runTransaction(async (transaction) => {
        const doc = await transaction.get(userProgressRef);
        const currentData: any = doc.exists ? doc.data() : {
          completedNodes: [],
          favorites: [],
          studyStreak: 0,
          totalReadingTime: 0,
          lastActivity: null
        };

        switch (action) {
          case 'complete':
            if (!currentData.completedNodes.includes(nodeId)) {
              currentData.completedNodes.push(nodeId);
            }
            break;
          case 'favorite':
            if (!currentData.favorites.includes(nodeId)) {
              currentData.favorites.push(nodeId);
            }
            break;
          case 'unfavorite':
            currentData.favorites = currentData.favorites.filter((id: any) => id !== nodeId);
            break;
        }

        if (readingTime) {
          currentData.totalReadingTime += readingTime;
        }

        // Update study streak
        const today = new Date().toDateString();
        const lastActivity = currentData.lastActivity ? new Date(currentData.lastActivity.toDate()).toDateString() : null;
        
        if (lastActivity !== today) {
          const yesterday = new Date();
          yesterday.setDate(yesterday.getDate() - 1);
          
          if (lastActivity === yesterday.toDateString()) {
            currentData.studyStreak += 1;
          } else if (lastActivity !== today) {
            currentData.studyStreak = 1;
          }
          
          currentData.lastActivity = new Date();
        }

        transaction.set(userProgressRef, currentData, { merge: true });
      });

      res.json({ success: true });
    } catch (error) {
      console.error("Error updating progress:", error);
      res.status(500).json({ error: "Failed to update progress" });
    }
  });

  // Create Stripe checkout session
  app.post("/api/create-checkout-session", async (req, res) => {
    try {
      if (!stripe) {
        return res.status(503).json({ error: "Stripe not configured" });
      }

      const { priceId, userId, successUrl, cancelUrl } = req.body;
      if (!priceId || !userId || !successUrl || !cancelUrl) {
        return res.status(400).json({ error: "Missing checkout session parameters" });
      }

      const session = await stripe.checkout.sessions.create({
        mode: 'subscription',
        payment_method_types: ['card'],
        line_items: [
          {
            price: priceId,
            quantity: 1,
          },
        ],
        metadata: {
          userId: userId,
        },
        success_url: successUrl,
        cancel_url: cancelUrl,
      });

      res.json({ sessionId: session.id, checkoutUrl: session.url });
    } catch (error) {
      console.error('Error creating checkout session:', error);
      res.status(500).json({ error: 'Failed to create checkout session' });
    }
  });

  // Verify user subscription status
  app.get("/api/check-subscription", async (req, res) => {
    try {
      if (!db) {
        return res.status(503).json({ error: "Database not available" });
      }

      const userId = String(req.query.userId || '');
      if (!userId) {
        return res.status(400).json({ error: "userId query parameter is required" });
      }

      const userDoc = await db.collection("users").doc(userId).get();
      if (!userDoc.exists) {
        return res.json({ premium: false });
      }

      const data: any = userDoc.data() || {};
      const isPremium = data.premium === true || data.subscriptionStatus === "active";
      res.json({
        premium: isPremium,
        expiresAt: data.subscriptionExpiresAt || undefined
      });
    } catch (error) {
      console.error("Error checking subscription:", error);
      res.status(500).json({ error: "Failed to check subscription" });
    }
  });

  // Analytics endpoint
  app.get("/api/analytics/:userId", async (req, res) => {
    try {
      if (!db) {
        return res.status(503).json({ error: "Database not available" });
      }

      const userId = req.params.userId;
      const progressDoc = await db.collection("userProgress").doc(userId).get();
      
      if (!progressDoc.exists) {
        return res.json({
          totalNodes: 0,
          completedNodes: 0,
          completionRate: 0,
          studyStreak: 0,
          totalReadingTime: 0,
          seriesProgress: []
        });
      }

      const progressData: any = progressDoc.data();
      const allNodesSnapshot = await db.collection("nodes").get();
      const allNodes = allNodesSnapshot.docs.map((doc: any) => ({ id: doc.id, ...doc.data() }));

      // Calculate series progress
      const seriesProgress: any = {};
      allNodes.forEach((node: any) => {
        const series = node.category || 'Unknown';
        if (!seriesProgress[series]) {
          seriesProgress[series] = { total: 0, completed: 0 };
        }
        seriesProgress[series].total++;
        if (progressData.completedNodes.includes(node.id)) {
          seriesProgress[series].completed++;
        }
      });

      res.json({
        totalNodes: allNodes.length,
        completedNodes: progressData.completedNodes.length,
        completionRate: allNodes.length > 0 ? (progressData.completedNodes.length / allNodes.length) * 100 : 0,
        studyStreak: progressData.studyStreak || 0,
        totalReadingTime: progressData.totalReadingTime || 0,
        seriesProgress: Object.entries(seriesProgress).map(([series, data]: [string, any]) => ({
          series,
          ...data,
          percentage: data.total > 0 ? (data.completed / data.total) * 100 : 0
        }))
      });
    } catch (error) {
      console.error("Error fetching analytics:", error);
      res.status(500).json({ error: "Failed to fetch analytics" });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
