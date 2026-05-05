import fs from 'fs';
import path from 'path';
import { initializeApp, cert, getApps } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';

/**
 * CLI Script to import data from fitlib_export.json into Firestore
 */
async function importData() {
  const filePath = path.join('/Users/enes/fitlibvault-main', 'fitlib_export.json');
  
  if (!fs.existsSync(filePath)) {
    console.error('❌ Error: fitlib_export.json not found in root directory.');
    process.exit(1);
  }

  const rawData = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(rawData);
  const serviceAccountRaw = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
  if (!serviceAccountRaw) {
    throw new Error('FIREBASE_SERVICE_ACCOUNT_KEY is required for import');
  }

  if (getApps().length === 0) {
    initializeApp({
      credential: cert(JSON.parse(serviceAccountRaw)),
    });
  }

  const db = getFirestore();

  console.log(`🚀 Starting import of ${data.nodes?.length || 0} nodes...`);

  // Using batches for efficiency (Firestore limit is 500 per batch)
  let batch = db.batch();
  let count = 0;
  let operations = 0;

  for (const node of data.nodes) {
    const { id, citations, ...nodeData } = node;
    const nodeRef = db.doc(`nodes/${id}`);
    
    batch.set(nodeRef, {
      ...nodeData,
      updatedAt: new Date().toISOString()
    });
    operations++;

    // Handle Citations if they exist in the export
    if (citations && citations.length > 0) {
      for (const citation of citations) {
        const citationId = citation.id || db.collection('_temp').doc().id;
        const citationRef = db.doc(`nodes/${id}/citations/${citationId}`);
        batch.set(citationRef, citation);
        operations++;
      }
    }

    count++;
    if (operations >= 450) {
      await batch.commit();
      batch = db.batch();
      operations = 0;
      console.log(`Imported ${count} nodes...`);
    }
  }

  if (operations > 0) {
    await batch.commit();
  }
  console.log(`✅ Import complete! ${count} markdown nodes are now live.`);
}

importData().catch((error) => {
  console.error('❌ Import failed:', error instanceof Error ? error.message : error);
  process.exit(1);
});
