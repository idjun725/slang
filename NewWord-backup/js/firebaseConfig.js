// firebaseConfig.js
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getFunctions } from 'firebase/functions';

const firebaseConfig = {
  apiKey: "AIzaSyAECRRXktRoo-eIF-Cz5AOb-Pv965m-yjQ",
  authDomain: "neologisms-6731a.firebaseapp.com",
  projectId: "neologisms-6731a",
  storageBucket: "neologisms-6731a.firebasestorage.app",
  messagingSenderId: "152259561768",
  appId: "1:152259561768:web:8d7f5583f5a60cecaae81d",
  measurementId: "G-RREL4MVBJY"
};

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export const functions = getFunctions(app, 'asia-northeast3');

export { RecaptchaVerifier, signInWithPhoneNumber };