"""
VolunteerBridge Seed Script
Run: python backend/seed.py
"""

import os
import sys
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "volunteerbridge"

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def rand_date(start_days: int, end_days: int) -> str:
    d = datetime.now() + timedelta(days=random.randint(start_days, end_days))
    return d.strftime("%Y-%m-%d")

def rand_time() -> str:
    h = random.choice([8, 9, 10, 11, 14, 15, 16])
    m = random.choice([0, 30])
    return f"{h:02d}:{m:02d}"

# ─── Seed Data ────────────────────────────────────────────────────────────────

NGO_DATA = [
    {"name": "Green Earth Foundation", "email": "admin@greenearth.org", "phone": "+1-212-555-0101", "address": "45 Park Ave, New York, NY 10016", "mission": "Protecting the environment through community action and education.", "website": "https://greenearth.org"},
    {"name": "Bright Futures Education", "email": "contact@brightfutures.edu", "phone": "+1-323-555-0202", "address": "120 Sunset Blvd, Los Angeles, CA 90028", "mission": "Providing quality education to underserved youth communities.", "website": "https://brightfutures.edu"},
    {"name": "City Food Bank Network", "email": "info@cityfoodbank.org", "phone": "+1-312-555-0303", "address": "800 S Michigan Ave, Chicago, IL 60605", "mission": "Ending hunger by connecting communities with nutritious food.", "website": "https://cityfoodbank.org"},
    {"name": "HealthBridge Initiative", "email": "hello@healthbridge.org", "phone": "+1-713-555-0404", "address": "2400 Main St, Houston, TX 77002", "mission": "Bringing accessible healthcare to rural and underserved populations.", "website": "https://healthbridge.org"},
    {"name": "Animal Haven Society", "email": "rescue@animalhaven.org", "phone": "+1-602-555-0505", "address": "550 Desert Dr, Phoenix, AZ 85001", "mission": "Rescuing and rehoming animals across the Southwest.", "website": "https://animalhaven.org"},
    {"name": "Arts & Culture Collective", "email": "art@acccollective.org", "phone": "+1-206-555-0606", "address": "300 1st Ave N, Seattle, WA 98109", "mission": "Making arts and cultural experiences accessible to everyone.", "website": "https://acccollective.org"},
    {"name": "Disaster Relief Coalition", "email": "respond@drcrelief.org", "phone": "+1-305-555-0707", "address": "100 SE 2nd St, Miami, FL 33131", "mission": "Rapid response and long-term recovery support for disaster survivors.", "website": "https://drcrelief.org"},
    {"name": "Youth Sports Academy", "email": "play@youthsports.org", "phone": "+1-617-555-0808", "address": "15 Commonwealth Ave, Boston, MA 02115", "mission": "Using sports to develop character, fitness, and opportunity in youth.", "website": "https://youthsports.org"},
    {"name": "Ocean Cleanup Alliance", "email": "ocean@cleanupalliance.org", "phone": "+1-858-555-0909", "address": "1200 Shoreline Dr, San Diego, CA 92101", "mission": "Removing plastic waste from oceans and coastal ecosystems.", "website": "https://cleanupalliance.org"},
]

EVENT_TEMPLATES = [
    {"name": "Community Park Cleanup", "type": "Community Service", "location": "Riverside Park, New York", "description": "Help us clean and restore Riverside Park. Bring gloves and wear sturdy shoes."},
    {"name": "After-School Tutoring Program", "type": "Education", "location": "Lincoln Elementary, Chicago", "description": "Tutor K-8 students in math and reading. No teaching experience required."},
    {"name": "Weekend Food Distribution", "type": "Food & Hunger", "location": "Union Square, San Francisco", "description": "Help pack and distribute food parcels to families in need."},
    {"name": "Free Health Screening Day", "type": "Healthcare", "location": "Community Center, Houston", "description": "Assist healthcare professionals in running free blood pressure and glucose screenings."},
    {"name": "Animal Shelter Volunteering", "type": "Animal Welfare", "location": "Desert Animal Shelter, Phoenix", "description": "Walk dogs, socialize cats, and help with shelter maintenance."},
    {"name": "Street Art Mural Project", "type": "Arts & Culture", "location": "Downtown Seattle", "description": "Paint a community mural celebrating local culture. All skill levels welcome."},
    {"name": "Beach Plastic Collection Drive", "type": "Environmental", "location": "Mission Beach, San Diego", "description": "Collect and sort plastic waste from the beach. Equipment provided."},
    {"name": "Disaster Preparedness Workshop", "type": "Disaster Relief", "location": "Miami Community Hall", "description": "Teach community members basic disaster preparedness and first aid."},
    {"name": "Youth Basketball Tournament", "type": "Sports & Recreation", "location": "Boston Sports Complex", "description": "Volunteer as referee, score keeper, or coordinator for a youth basketball tournament."},
    {"name": "Reforestation Tree Planting", "type": "Environmental", "location": "Angeles National Forest, CA", "description": "Plant native trees to restore wildfire-damaged areas. Lunch provided."},
    {"name": "Digital Literacy for Seniors", "type": "Education", "location": "Downtown Library, New York", "description": "Help seniors learn to use smartphones, tablets, and the internet safely."},
    {"name": "Soup Kitchen Serving Day", "type": "Food & Hunger", "location": "Grace Mission, Chicago", "description": "Prepare and serve hot meals to over 200 guests. Morning shifts available."},
    {"name": "Mental Health Awareness Walk", "type": "Healthcare", "location": "Golden Gate Park, San Francisco", "description": "Organize and participate in a community awareness walk for mental health advocacy."},
    {"name": "Pet Adoption Fair", "type": "Animal Welfare", "location": "Tempe Town Lake, AZ", "description": "Help showcase adoptable pets and connect them with loving families."},
    {"name": "Cultural Heritage Festival", "type": "Arts & Culture", "location": "Pike Place Market, Seattle", "description": "Assist with setup, performances, and food stalls at a multicultural community festival."},
    {"name": "Neighborhood Graffiti Removal", "type": "Community Service", "location": "East LA Community, CA", "description": "Help beautify the neighborhood by removing graffiti from public spaces."},
    {"name": "Flood Recovery Clean-Up", "type": "Disaster Relief", "location": "Fort Lauderdale, FL", "description": "Assist flood-affected residents with debris removal and home cleaning."},
    {"name": "Kids Soccer Coaching Camp", "type": "Sports & Recreation", "location": "Harvard Fields, Boston", "description": "Coach youth soccer players aged 6-12. Training provided on the day."},
    {"name": "River Water Quality Monitoring", "type": "Environmental", "location": "Colorado River, AZ", "description": "Help scientists collect water samples and record environmental data."},
    {"name": "Coding Bootcamp for Teens", "type": "Education", "location": "Tech Hub, San Diego", "description": "Teach teens basic HTML, CSS, and Python in a fun, hands-on bootcamp."},
]

VOLUNTEER_DATA = [
    {"name": "Alice Johnson", "email": "alice.j@volunteers.com", "location": "New York, NY", "skills": ["Teaching", "First Aid"], "description": "Passionate educator with 5 years of tutoring experience."},
    {"name": "Benjamin Carter", "email": "ben.carter@volunteers.com", "location": "Chicago, IL", "skills": ["Cooking", "Food Safety"], "description": "Amateur chef who loves helping at community kitchens."},
    {"name": "Carmen Diaz", "email": "carmen.d@volunteers.com", "location": "Los Angeles, CA", "skills": ["Spanish", "Community Outreach"], "description": "Bilingual advocate for underserved Latino communities."},
    {"name": "David Kim", "email": "david.k@volunteers.com", "location": "Houston, TX", "skills": ["Nursing", "CPR", "First Aid"], "description": "Registered nurse with experience in mobile health clinics."},
    {"name": "Emily Zhang", "email": "emily.z@volunteers.com", "location": "San Francisco, CA", "skills": ["Python", "Web Development", "Data Analysis"], "description": "Software engineer who enjoys using tech for social good."},
    {"name": "Frank Martin", "email": "frank.m@volunteers.com", "location": "Phoenix, AZ", "skills": ["Animal Care", "Dog Training"], "description": "Certified dog trainer and animal welfare advocate."},
    {"name": "Grace Lee", "email": "grace.l@volunteers.com", "location": "Seattle, WA", "skills": ["Painting", "Photography", "Event Planning"], "description": "Graphic designer passionate about public art projects."},
    {"name": "Henry Brown", "email": "henry.b@volunteers.com", "location": "Miami, FL", "skills": ["Construction", "Carpentry", "Disaster Relief"], "description": "Contractor with experience in post-hurricane rebuilding."},
    {"name": "Isabella Ross", "email": "isabella.r@volunteers.com", "location": "Boston, MA", "skills": ["Sports Coaching", "Youth Mentoring"], "description": "Former collegiate athlete who now coaches youth sports."},
    {"name": "James Thompson", "email": "james.t@volunteers.com", "location": "San Diego, CA", "skills": ["Marine Biology", "Environmental Science"], "description": "PhD student studying ocean pollution and marine ecosystems."},
    {"name": "Karen White", "email": "karen.w@volunteers.com", "location": "New York, NY", "skills": ["Social Work", "Community Organizing"], "description": "Licensed social worker specializing in family services."},
    {"name": "Liam Garcia", "email": "liam.g@volunteers.com", "location": "Chicago, IL", "skills": ["Teaching", "Math", "Science"], "description": "High school math teacher who volunteers during summers."},
    {"name": "Mia Wilson", "email": "mia.w@volunteers.com", "location": "Houston, TX", "skills": ["Healthcare", "Patient Care", "Elderly Care"], "description": "Medical student with a passion for community health."},
    {"name": "Noah Davis", "email": "noah.d@volunteers.com", "location": "Phoenix, AZ", "skills": ["Animal Rescue", "Veterinary Assistance"], "description": "Vet tech who spends weekends at the local animal shelter."},
    {"name": "Olivia Martinez", "email": "olivia.m@volunteers.com", "location": "Los Angeles, CA", "skills": ["Fundraising", "Marketing", "Social Media"], "description": "Non-profit marketing manager looking to give back."},
    {"name": "Patrick Nguyen", "email": "patrick.n@volunteers.com", "location": "Seattle, WA", "skills": ["Coding", "HTML", "JavaScript"], "description": "Full-stack developer passionate about tech education for youth."},
    {"name": "Quinn Baker", "email": "quinn.b@volunteers.com", "location": "Miami, FL", "skills": ["First Aid", "Lifeguarding", "Swimming"], "description": "Certified lifeguard and water safety instructor."},
    {"name": "Rachel Scott", "email": "rachel.s@volunteers.com", "location": "Boston, MA", "skills": ["Photography", "Video Editing", "Social Media"], "description": "Documentary filmmaker focused on social justice stories."},
    {"name": "Samuel Adams", "email": "samuel.a@volunteers.com", "location": "San Diego, CA", "skills": ["Diving", "Ocean Conservation", "Data Collection"], "description": "Avid scuba diver and ocean conservationist."},
    {"name": "Tina Lee", "email": "tina.l@volunteers.com", "location": "New York, NY", "skills": ["Cooking", "Nutrition", "Food Safety"], "description": "Registered dietitian who volunteers at food banks."},
    {"name": "Umar Patel", "email": "umar.p@volunteers.com", "location": "Chicago, IL", "skills": ["Logistics", "Driving", "Warehouse"], "description": "Logistics coordinator for a major distribution company."},
    {"name": "Victoria Chen", "email": "victoria.c@volunteers.com", "location": "Houston, TX", "skills": ["Mandarin", "English", "Teaching"], "description": "ESL teacher helping immigrant communities adapt."},
    {"name": "William Turner", "email": "william.t@volunteers.com", "location": "Los Angeles, CA", "skills": ["Construction", "Plumbing", "Electrical"], "description": "General contractor who rebuilds homes for disaster victims."},
    {"name": "Xena Rodriguez", "email": "xena.r@volunteers.com", "location": "Phoenix, AZ", "skills": ["Outreach", "Crisis Counseling", "Spanish"], "description": "Crisis counselor with 8 years of field experience."},
    {"name": "Yusuf Hassan", "email": "yusuf.h@volunteers.com", "location": "Seattle, WA", "skills": ["Soccer", "Youth Coaching", "Arabic"], "description": "Soccer coach and youth mentor in refugee communities."},
    {"name": "Zoe Campbell", "email": "zoe.c@volunteers.com", "location": "Miami, FL", "skills": ["Marine Conservation", "Diving", "Environmental Education"], "description": "Marine biologist with a passion for reef restoration."},
    {"name": "Aaron Foster", "email": "aaron.f@volunteers.com", "location": "Boston, MA", "skills": ["Event Management", "Volunteer Coordination"], "description": "Event manager who loves organizing community events."},
    {"name": "Bella Young", "email": "bella.y@volunteers.com", "location": "San Diego, CA", "skills": ["Graphic Design", "Painting", "Murals"], "description": "Street artist who transforms blank walls into community art."},
    {"name": "Carlos Reyes", "email": "carlos.r@volunteers.com", "location": "New York, NY", "skills": ["Elderly Care", "Driving", "Errand Running"], "description": "Retired postal worker who helps elderly neighbors."},
    {"name": "Diana Harper", "email": "diana.h@volunteers.com", "location": "Chicago, IL", "skills": ["Psychology", "Mentoring", "Youth Programs"], "description": "Child psychologist running after-school programs."},
]


def run():
    if not MONGO_URI:
        print("ERROR: MONGO_URI environment variable not set.")
        sys.exit(1)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    print("Connected to MongoDB. Clearing existing seed data...")
    db.ngos.delete_many({"_seeded": True})
    db.volunteers.delete_many({"_seeded": True})
    db.events.delete_many({"_seeded": True})
    db.applications.delete_many({"_seeded": True})
    db.ratings.delete_many({"_seeded": True})

    # ─── Insert NGOs ──────────────────────────────────────────────────────────
    print("Inserting NGOs...")
    ngo_ids = []
    for n in NGO_DATA:
        doc = {**n, "password": hash_pw("Password123!"), "role": "ngo", "_seeded": True}
        r = db.ngos.insert_one(doc)
        ngo_ids.append(r.inserted_id)
    print(f"  → {len(ngo_ids)} NGOs created")

    # ─── Insert Volunteers ────────────────────────────────────────────────────
    print("Inserting volunteers...")
    vol_ids = []
    for v in VOLUNTEER_DATA:
        doc = {**v, "password": hash_pw("Password123!"), "role": "volunteer", "rating": None, "_seeded": True}
        r = db.volunteers.insert_one(doc)
        vol_ids.append(r.inserted_id)
    print(f"  → {len(vol_ids)} volunteers created")

    # ─── Insert Events ─────────────────────────────────────────────────────────
    print("Inserting events...")
    now = datetime.now(timezone.utc)

    statuses = (
        ["Completed"] * 7 +
        ["Applications Closed"] * 5 +
        ["Open"] * 8
    )
    random.shuffle(statuses)

    event_ids = []
    event_statuses = []
    for i, tmpl in enumerate(EVENT_TEMPLATES):
        status = statuses[i % len(statuses)]
        if status == "Completed":
            event_date = rand_date(-60, -5)
        elif status == "Applications Closed":
            event_date = rand_date(-5, 10)
        else:
            event_date = rand_date(5, 90)

        ngo_id = ngo_ids[i % len(ngo_ids)]
        doc = {
            **tmpl,
            "date": event_date,
            "time": rand_time(),
            "ngoId": ngo_id,
            "status": status,
            "createdAt": now,
            "_seeded": True,
        }
        r = db.events.insert_one(doc)
        event_ids.append(r.inserted_id)
        event_statuses.append(status)
    print(f"  → {len(event_ids)} events created")

    # ─── Insert Applications ──────────────────────────────────────────────────
    print("Inserting applications...")
    app_count = 0
    # Store (event_idx, vol_id, app_id, app_status)
    accepted_in_completed = []

    for ev_idx, (event_id, ev_status) in enumerate(zip(event_ids, event_statuses)):
        # Each event gets 3-8 applicants
        num_applicants = random.randint(3, 8)
        applicants = random.sample(vol_ids, min(num_applicants, len(vol_ids)))

        for vol_id in applicants:
            if ev_status == "Completed":
                app_status = random.choices(["Accepted", "Rejected", "Pending"], weights=[50, 35, 15])[0]
            elif ev_status == "Applications Closed":
                app_status = random.choices(["Accepted", "Rejected", "Pending"], weights=[40, 40, 20])[0]
            else:
                app_status = "Pending"

            app_doc = {
                "eventId": event_id,
                "volunteerId": vol_id,
                "status": app_status,
                "createdAt": now,
                "_seeded": True,
            }
            r = db.applications.insert_one(app_doc)
            app_count += 1

            if ev_status == "Completed" and app_status == "Accepted":
                accepted_in_completed.append({
                    "event_id": event_id,
                    "ngo_id": ngo_ids[ev_idx % len(ngo_ids)],
                    "vol_id": vol_id,
                })

    print(f"  → {app_count} applications created")

    # ─── Insert Ratings ────────────────────────────────────────────────────────
    print("Inserting ratings and updating volunteer averages...")
    rated_combos = set()
    rating_count = 0
    vol_ratings: dict = {vid: [] for vid in vol_ids}

    for item in accepted_in_completed:
        key = (item["event_id"], item["vol_id"])
        if key in rated_combos:
            continue
        if random.random() < 0.75:  # 75% of accepted volunteers get rated
            stars = random.randint(3, 5)
            db.ratings.insert_one({
                "eventId": item["event_id"],
                "ngoId": item["ngo_id"],
                "volunteerId": item["vol_id"],
                "rating": stars,
                "createdAt": now,
                "_seeded": True,
            })
            rated_combos.add(key)
            vol_ratings[item["vol_id"]].append(stars)
            rating_count += 1

    # Update volunteer average ratings
    for vol_id, ratings_list in vol_ratings.items():
        if ratings_list:
            avg = round(sum(ratings_list) / len(ratings_list), 2)
            db.volunteers.update_one({"_id": vol_id}, {"$set": {"rating": avg}})

    print(f"  → {rating_count} ratings created")

    print("\n✅ Seed complete!")
    print(f"   {len(ngo_ids)} NGOs  |  {len(vol_ids)} volunteers  |  {len(event_ids)} events  |  {app_count} applications  |  {rating_count} ratings")
    print("\nDefault password for all seeded accounts: Password123!")
    print("\nSample NGO logins:")
    for n in NGO_DATA[:3]:
        print(f"  {n['email']}  (role: ngo)")
    print("\nSample Volunteer logins:")
    for v in VOLUNTEER_DATA[:3]:
        print(f"  {v['email']}  (role: volunteer)")

    client.close()


if __name__ == "__main__":
    run()
