import os
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore, storage

_db = None
_bucket = None


def _resolve_cred_path() -> str:
    cred_path = (
        os.getenv("FIREBASE_CRED")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or "serviceAccountKey.json"
    )

    cred_path = cred_path.strip().strip('"').strip("'")

    print(f"FIREBASE_CRED resolved to: {cred_path}", flush=True)
    print(f"FIREBASE_STORAGE_BUCKET: {os.getenv('FIREBASE_STORAGE_BUCKET')}", flush=True)

    return cred_path


def get_db():
    global _db

    if _db is not None:
        print("Firestore DB already initialized", flush=True)
        return _db

    print("Initializing Firestore...", flush=True)

    cred_path = _resolve_cred_path()

    if not os.path.exists(cred_path):
        raise RuntimeError(
            f"Firebase credential file not found: {cred_path}\n"
            f"Set FIREBASE_CRED to an absolute path, e.g.\n"
            f'  FIREBASE_CRED="/etc/secrets/serviceAccountKey.json"\n'
            f"Or place serviceAccountKey.json in the backend working directory."
        )

    print("Firebase credential file exists ✅", flush=True)

    cred = credentials.Certificate(cred_path)
    print("Firebase credential loaded ✅", flush=True)

    if not firebase_admin._apps:
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        init_opts = {}

        if bucket_name:
            init_opts["storageBucket"] = bucket_name
            print(f"Initializing Firebase with bucket: {bucket_name}", flush=True)
        else:
            print("Initializing Firebase without storage bucket", flush=True)

        firebase_admin.initialize_app(cred, init_opts)
        print("Firebase app initialized ✅", flush=True)
    else:
        print("Firebase app already exists ✅", flush=True)

    _db = firestore.client()
    print("Firestore client created ✅", flush=True)

    return _db


def get_bucket():
    global _bucket

    if _bucket is not None:
        return _bucket

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

    if not bucket_name:
        raise RuntimeError("FIREBASE_STORAGE_BUCKET is not set. Storage uploads will fail.")

    # مهم: يضمن أن firebase_admin.initialize_app اشتغل قبل storage.bucket()
    get_db()

    _bucket = storage.bucket()
    print(f"Firebase Storage bucket ready ✅: {bucket_name}", flush=True)

    return _bucket


def fetch_all_faq():
    print("Fetching FAQ from Firestore...", flush=True)

    db = get_db()
    docs = db.collection("faq").stream()

    items = []
    for d in docs:
        data = d.to_dict() or {}
        items.append({
            "id": d.id,
            "question": data.get("question", ""),
            "answer": data.get("answer", ""),
            "category": data.get("category", ""),
        })

    print(f"FAQ fetched ✅ count={len(items)}", flush=True)
    return items


def save_lost_found_report(report: dict):
    print("Saving lost found report...", flush=True)

    db = get_db()
    ticket_id = report["ticket_id"]
    db.collection("lost_found_reports").document(ticket_id).set(report)

    print(f"Lost found report saved ✅ ticket_id={ticket_id}", flush=True)


def get_lost_found_report(ticket_id: str):
    print(f"Getting lost found report: {ticket_id}", flush=True)

    db = get_db()
    doc = db.collection("lost_found_reports").document(ticket_id).get()

    if not doc.exists:
        print("Lost found report not found", flush=True)
        return None

    print("Lost found report loaded ✅", flush=True)
    return doc.to_dict()


def get_passenger_reports(passenger_id: str) -> list:
    print(f"Getting passenger reports for: {passenger_id}", flush=True)

    db = get_db()

    docs = (
        db.collection("lost_found_reports")
        .where("passenger_id", "==", passenger_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )

    reports = []
    for d in docs:
        data = d.to_dict() or {}
        reports.append(data)

    print(f"Passenger reports fetched ✅ count={len(reports)}", flush=True)
    return reports
