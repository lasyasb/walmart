// Firebase Firestore Security Rules for CoBudget
// Copy and paste these rules into your Firebase Console > Firestore Database > Rules

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Budgets collection - users can only access their own budget
    match /budgets/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Personal cart collection - users can only access their own cart items
    match /cart/{cartId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.userId;
      allow create: if request.auth != null && request.auth.uid == request.resource.data.userId;
    }
    
    // Shared cart collection - all authenticated users can read/write
    match /shared_cart/{sharedCartId} {
      allow read, write: if request.auth != null;
    }
    
    // Products collection - read-only for all authenticated users
    match /products/{productId} {
      allow read: if request.auth != null;
    }
    
    // Recommendation logs - users can only create logs, admin can read all
    match /recommendation_logs/{logId} {
      allow create: if request.auth != null;
      allow read: if request.auth != null; // Can be restricted to admin only
    }
    
    // Default deny all other documents
    match /{document=**} {
      allow read, write: if false;
    }
  }
}