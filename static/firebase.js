// Firebase Web SDK v11+ configuration and exports
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.9.1/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/11.9.1/firebase-auth.js";
import {
  getFirestore,
  collection,
  addDoc,
  getDocs,
  getDoc,
  setDoc,
  deleteDoc,
  query,
  where,
  doc
} from "https://www.gstatic.com/firebasejs/11.9.1/firebase-firestore.js";

// Firebase configuration - using environment variables
const firebaseConfig = {
  apiKey: window.FIREBASE_API_KEY,
  authDomain: `${window.FIREBASE_PROJECT_ID}.firebaseapp.com`,
  projectId: window.FIREBASE_PROJECT_ID,
  storageBucket: `${window.FIREBASE_PROJECT_ID}.firebasestorage.app`,
  appId: window.FIREBASE_APP_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Export Firebase services and functions
export {
  auth, 
  db,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  collection, 
  addDoc, 
  getDocs, 
  getDoc,
  setDoc, 
  deleteDoc, 
  query, 
  where,
  doc
};
