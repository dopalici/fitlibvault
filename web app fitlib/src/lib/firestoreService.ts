import { initializeApp } from 'firebase/app';
import { getFirestore, collection, query, where, getDocs, doc, setDoc, updateDoc, getDoc } from 'firebase/firestore';
import { getAuth, signOut, onAuthStateChanged, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { NodeData } from '../types';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);

// Load all nodes from Firestore
export async function loadAllNodes(): Promise<NodeData[]> {
  const nodesRef = collection(db, 'nodes');
  const snapshot = await getDocs(nodesRef);
  return snapshot.docs.map(doc => ({
    ...doc.data(),
    id: doc.id,
  } as NodeData));
}

// Search nodes by title/content
export async function searchNodes(query_term: string): Promise<NodeData[]> {
  const nodes = await loadAllNodes();
  const lowerQuery = query_term.toLowerCase();
  return nodes.filter(node => 
    node.title.toLowerCase().includes(lowerQuery) ||
    node.content.toLowerCase().includes(lowerQuery)
  );
}

// Get single node by ID
export async function getNodeById(id: string): Promise<NodeData | null> {
  const docRef = doc(db, 'nodes', id);
  const docSnap = await getDoc(docRef);
  return docSnap.exists() ? (docSnap.data() as NodeData) : null;
}

// Import nodes from extraction
export async function importNodesFromExtract(nodes: NodeData[]): Promise<void> {
  const batch = [];
  for (const node of nodes) {
    const docRef = doc(db, 'nodes', node.id);
    batch.push(setDoc(docRef, node));
  }
  await Promise.all(batch);
  console.log(`✅ Imported ${nodes.length} nodes to Firestore`);
}

// User preferences
export async function saveUserPreference(userId: string, preferences: any): Promise<void> {
  const userRef = doc(db, 'users', userId);
  await setDoc(userRef, preferences, { merge: true });
}

export async function getUserPreference(userId: string): Promise<any> {
  const userRef = doc(db, 'users', userId);
  const docSnap = await getDoc(userRef);
  return docSnap.exists() ? docSnap.data() : {};
}

// Premium status
export async function setPremiumStatus(userId: string, premium: boolean): Promise<void> {
  await saveUserPreference(userId, { premium, updatedAt: new Date() });
}

export async function isPremiumUser(userId: string): Promise<boolean> {
  const prefs = await getUserPreference(userId);
  return prefs.premium === true;
}

// Firebase Auth with Google
export async function signInWithGoogle(auth: any) {
  const provider = new GoogleAuthProvider();
  return signInWithPopup(auth, provider);
}

export { signOut, onAuthStateChanged };
