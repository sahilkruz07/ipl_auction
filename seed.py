# """Idempotent seed script. Safe to re-run: existing documents are never overwritten
# (passwords, purse values, auction results and bets are preserved)."""
# import secrets
# import uuid
#
# from werkzeug.security import generate_password_hash
#
# from app import DEFAULT_RULES, db, ensure_indexes
#
# TEAMS = [  # team_name, full_name, purse, slots, overseas
#     ("LSG", "Lucknow Super Giants", 47.45, 7, 3),
#     ("KKR", "Kolkata Knight Riders", 41.65, 8, 3),
#     ("SRH", "Sunrisers Hyderabad", 40.15, 7, 3),
#     ("DC", "Delhi Capitals", 39.50, 9, 4),
#     ("MI", "Mumbai Indians", 32.60, 9, 2),
#     ("CSK", "Chennai Super Kings", 28.05, 6, 2),
#     ("RR", "Rajasthan Royals", 27.05, 6, 3),
#     ("PBKS", "Punjab Kings", 18.60, 6, 2),
#     ("RCB", "Royal Challengers Bengaluru", 14.15, 5, 1),
#     ("GT", "Gujarat Titans", 8.75, 3, 2),
# ]
#
# # Illustrative sample pool (not an official list). (name, overseas, role)
# PLAYERS = [
#     ("Venkatesh Iyer", False, "allrounder"),
#     ("Ravi Bishnoi", False, "bowler"),
#     ("Washington Sundar", False, "allrounder"),
#     ("Prithvi Shaw", False, "batter"),
#     ("Mayank Agarwal", False, "batter"),
#     ("Deepak Chahar", False, "bowler"),
#     ("Rahul Chahar", False, "bowler"),
#     ("Sarfaraz Khan", False, "batter"),
#     ("Ishan Kishan", False, "wicket keeper"),
#     ("Jitesh Sharma", False, "wicket keeper"),
#     ("Cameron Green", True, "allrounder"),
#     ("Liam Livingstone", True, "allrounder"),
#     ("Jake Fraser-McGurk", True, "batter"),
#     ("Mitchell Starc", True, "bowler"),
#     ("Anrich Nortje", True, "bowler"),
#     ("Rachin Ravindra", True, "allrounder"),
#     ("Jonny Bairstow", True, "wicket keeper"),
#     ("Quinton de Kock", True, "wicket keeper"),
#     ("Wanindu Hasaranga", True, "allrounder"),
#     ("Matheesha Pathirana", True, "bowler"),
# ]
#
# USERS = [
#     ("admin", "Auction Admin", "admin"),
#     ("alice", "Alice", "player"),
#     ("bob", "Bob", "player"),
#     ("charlie", "Charlie", "player"),
# ]
#
#
# def main():
#     ensure_indexes()
#
#     db.config.update_one({"key": "edit_cutoff_flag"}, {"$setOnInsert": {"value": False}}, upsert=True)
#     db.config.update_one({"key": "scoring_rules"}, {"$setOnInsert": {"value": DEFAULT_RULES}}, upsert=True)
#
#     for name, full, purse, slots, overseas in TEAMS:
#         db.teamData.update_one(
#             {"team_name": name},
#             {"$setOnInsert": {"full_name": full, "purse_left": purse,
#                               "available_slots": slots, "overseas_slots": overseas}},
#             upsert=True)
#
#     for i, (name, overseas, role) in enumerate(PLAYERS, 1):
#         db.playerList.update_one(
#             {"player_id": str(i)},
#             {"$setOnInsert": {"player_name": name, "is_overseas": overseas, "role": role,
#                               "sold_to": None, "sold_price": None}},
#             upsert=True)
#
#     print("\nUsers")
#     print("-" * 44)
#     for username, display, role in USERS:
#         password = secrets.token_urlsafe(9)
#         res = db.users.update_one(
#             {"username": username},
#             {"$setOnInsert": {"user_id": str(uuid.uuid4()), "displayname": display,
#                               "role": role, "password": generate_password_hash(password)}},
#             upsert=True)
#         if res.upserted_id:
#             print(f"{role:<7} {username:<10} password: {password}")
#         else:
#             print(f"{role:<7} {username:<10} already exists (password unchanged)")
#     print("-" * 44)
#     print("Credentials are shown only when a user is first created.\n")
#     print(f"Seeded: {db.teamData.count_documents({})} teams, "
#           f"{db.playerList.count_documents({})} players.")
#
#
# if __name__ == "__main__":
#     main()
