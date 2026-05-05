import { setDoc, doc, collection } from 'firebase/firestore';
import { db } from '../lib/firebase';
import { MOCK_NODES } from '../data/mockNodes';

export async function seedDatabase() {
  console.log('Starting seed...');
  for (const node of MOCK_NODES) {
    const { id, citations, ...nodeData } = node;
    await setDoc(doc(db, 'nodes', id), nodeData);
    
    // Add citations to subcollection
    for (const citation of citations) {
      const { id: citationId, ...citData } = citation;
      await setDoc(doc(db, `nodes/${id}/citations`, citationId), citData);
    }
  }
  console.log('Seed complete!');
}
