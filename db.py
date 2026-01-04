from google.cloud import firestore

# Firestore client
# Uses gcloud auth locally
# Uses service account automatically on Cloud Run
db = firestore.Client(project="wastetrace")


# Collections
tickets_ref = db.collection("waste_tickets")
users_ref = db.collection("users")
locations_ref = db.collection("location_logs")
