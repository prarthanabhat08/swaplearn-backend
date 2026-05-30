from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, Skill, UserSkill, UserFullData, SkillRequest, ChatRoom, Message, UserProfile
import json
import hashlib
import os
from django.db.models import Q
from django.db.models import Count
print("RUNNING FROM:", os.getcwd())
print("CORRECT VIEWS.PY RUNNING ")    
from decouple import config

def home(request):
    return render(request, 'add.html')


@csrf_exempt
def register(request):
    if request.method == "POST":
        raw_password = request.POST.get("password")
        hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()

        user = User.objects.create(
            full_name=request.POST.get("name"),
            username=request.POST.get("username"),
            email=request.POST.get("email"),
            password=hashed_password
        )

        UserProfile.objects.create(
            user=user,
            username=user.username,
            credit=10,
            skills_learn_count=0,
            skills_teach_count=0
        )
       
        return render(request, 'success.html')

    return JsonResponse({"error": "POST required"}, status=400)


@csrf_exempt
def api_add_user(request):
    try:
        print("===== ADD USER HIT =====")

        data = json.loads(request.body)
        print("DATA:", data)

        hashed_password = hashlib.sha256(
            data.get("password").encode()
        ).hexdigest()

        user = User.objects.create(
            full_name=data.get("name"),
            username=data.get("username"),
            email=data.get("email"),
            password=hashed_password
        )

        print("USER CREATED:", user.user_id, user.username)

        count = User.objects.count()
        print("TOTAL USERS:", count)

        return JsonResponse({
            "success": True,
            "id": user.user_id
        })

    except Exception as e:
        print("ADD USER ERROR:", str(e))
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


# ================= LOGIN =================
@csrf_exempt
def api_login(request):
    if request.method == "POST":
        data = json.loads(request.body)

        hashed_password = hashlib.sha256(data.get("password").encode()).hexdigest()

        user = User.objects.filter(
            username=data.get("username"),
            password=hashed_password
        ).first()

        if user:
            return JsonResponse({
                "status": "success",
                "user_id": user.user_id,
                "name": user.full_name
            })

        return JsonResponse({"status": "error"})

    return JsonResponse({"error": "POST only"}, status=400)


# ================= REQUEST =================
def api_get_users(request):
    users = User.objects.all()

    return JsonResponse([
        {
            "user_id": u.user_id,
            "name": u.full_name,
            "email": u.email
        }
        for u in users
    ], safe=False)


@csrf_exempt
def send_request(request):
    if request.method == "POST":
        data = json.loads(request.body)

        sender = User.objects.get(user_id=data.get("sender_id"))
        receiver = User.objects.get(user_id=data.get("receiver_id"))

        skill = Skill.objects.filter(
            skill_name=data.get("skill"),
            language=data.get("language")
        ).first()

        SkillRequest.objects.create(
            sender=sender,
            receiver=receiver,
            skill=skill,
            status="pending"
        )

        return JsonResponse({"message": "Request sent"})

    return JsonResponse({"error": "POST only"}, status=400)


def get_requests(request, user_id):
    reqs = SkillRequest.objects.filter(receiver__user_id=user_id)

    return JsonResponse([
        {
            "request_id": r.request_id,
            "sender_name": r.sender.full_name,
            "skill": r.skill.skill_name,
            "status": r.status
        }
        for r in reqs
    ], safe=False)


# ================= ACCEPT REQUEST =================
@csrf_exempt
def accept_request(request):
    if request.method == "POST":
        data = json.loads(request.body)

        req = SkillRequest.objects.get(request_id=data.get("request_id"))
        if req.status != "accepted":
            req.status = "accepted"
            req.save()

        sender = req.sender
        receiver = req.receiver

        rooms = ChatRoom.objects.all()
        existing_room = None

        for room in rooms:
            users = list(room.users.all())
            user_ids = [u.user_id for u in users]

            if sender.user_id in user_ids and receiver.user_id in user_ids:
                existing_room = room
                break

        if not existing_room:
            room = ChatRoom.objects.create()
            room.users.add(sender)
            room.users.add(receiver)

            print("ROOM CREATED:", room.id)
        else:
            print("ROOM EXISTS:", existing_room.id)

        return JsonResponse({"message": "Accepted + chat ready"})

    return JsonResponse({"error": "POST only"}, status=400)


def get_chats(request, user_id):
    try:
        data = []

        rooms = ChatRoom.objects.all()

        for room in rooms:
            users = list(room.users.all())
            user_ids = [u.user_id for u in users]

            if int(user_id) not in user_ids:
                continue

            other_user = None
            for u in users:
                if u.user_id != int(user_id):
                    other_user = u
                    break

            if other_user:
                data.append({
                    "room_id": room.id,
                    "name": other_user.full_name,
                    "last_message": ""
                })

        print("FINAL CHAT LIST:", data)

        return JsonResponse(data, safe=False)

    except Exception as e:
        print("ERROR:", e)
        return JsonResponse({"error": str(e)}, status=500)


def get_messages(request, room_id):
    print(" FETCHING MESSAGES FOR ROOM:", room_id)

    msgs = Message.objects.filter(room__id=room_id).order_by("timestamp")

    print("MESSAGES:", msgs.count())

    return JsonResponse([
        {
            "sender": m.sender.user_id,
            "text": m.text
        }
        for m in msgs
    ], safe=False)

# ================= SEND MESSAGE =================
@csrf_exempt
def send_message(request):
    if request.method == "POST":
        data = json.loads(request.body)

        sender = User.objects.get(user_id=data.get("sender_id"))
        room = ChatRoom.objects.get(id=data.get("room_id"))

        Message.objects.create(
            sender=sender,
            room=room,
            text=data.get("text"),
            type=data.get("type", "text"),
            status="pending"
        )

        return JsonResponse({"message": "sent"})

    return JsonResponse({"error": "POST only"}, status=400)


# ================= SKILLS =================
@csrf_exempt
def save_user_skills(request):
    if request.method == "POST":
        data = json.loads(request.body)

        user = User.objects.get(user_id=data.get("user_id"))

        for s in data.get("teach_skills", []):
            skill, _ = Skill.objects.get_or_create(
                skill_name=s["skill"],
                category=s.get("category", "General"),
                language=s["language"]
            )
            UserSkill.objects.get_or_create(user=user, skill=skill, skill_type="teach")

        for s in data.get("learn_skills", []):
            skill, _ = Skill.objects.get_or_create(
                skill_name=s["skill"],
                category=s.get("category", "General"),
                language=s["language"]
            )
            UserSkill.objects.get_or_create(user=user, skill=skill, skill_type="learn")

        return JsonResponse({"message": "Saved"})

    return JsonResponse({"error": "POST only"}, status=400)


def get_user_skills(request, user_id):
    skills = UserSkill.objects.filter(user__user_id=user_id)

    return JsonResponse([
        {
            "skill_name": s.skill.skill_name,
            "category": s.skill.category,
            "language": s.skill.language,
            "type": s.skill_type
        }
        for s in skills
    ], safe=False)


def find_matches(request, user_id):
    user = User.objects.get(user_id=user_id)

    learn_skills = UserSkill.objects.filter(user=user, skill_type="learn")

    matches = []

    for ls in learn_skills:
        teachers = UserSkill.objects.filter(
            skill=ls.skill,
            skill_type="teach"
        ).exclude(user=user)

        for t in teachers:
            matches.append({
                "user_id": t.user.user_id,
                "name": t.user.full_name,
                "skill": ls.skill.skill_name,
                "language": ls.skill.language
            })

    return JsonResponse(matches, safe=False)


@csrf_exempt
def reject_request(request):
    if request.method == "POST":
        data = json.loads(request.body)

        req = SkillRequest.objects.get(request_id=data.get("request_id"))
        req.status = "rejected"
        req.save()

        return JsonResponse({"message": "Request rejected"})

    return JsonResponse({"error": "POST only"}, status=400)


def discover_users(request, user_id):
    users = User.objects.exclude(user_id=user_id)

    result = []

    for u in users:
        teach = UserSkill.objects.filter(user=u, skill_type="teach")
        learn = UserSkill.objects.filter(user=u, skill_type="learn")

        result.append({
            "user_id": u.user_id,
            "name": u.full_name,
            "teach": [t.skill.skill_name for t in teach],
            "learn": [l.skill.skill_name for l in learn],
        })

    return JsonResponse(result, safe=False)

@csrf_exempt
def update_profile(request):
    if request.method == "POST":
        data = json.loads(request.body)

        user = User.objects.get(user_id=data["user_id"])

        user.username = data["name"]
        user.email = data["email"]
        user.save()

        teach = data.get("teachSkills", [])
        learn = data.get("learnSkills", [])

        for s in teach:
            skill_obj, _ = Skill.objects.get_or_create(
                skill_name=s["skill"],
                language=s["language"]
            )

            if not UserSkill.objects.filter(
                user=user,
                skill=skill_obj,
                skill_type="teach"
            ).exists():

                UserSkill.objects.create(
                    user=user,
                    skill=skill_obj,
                    skill_type="teach"
                )


        for s in learn:
            skill_obj, _ = Skill.objects.get_or_create(
                skill_name=s["skill"],
                language=s["language"]
            )

            if not UserSkill.objects.filter(
                user=user,
                skill=skill_obj,
                skill_type="learn"
            ).exists():

                UserSkill.objects.create(
                    user=user,
                    skill=skill_obj,
                    skill_type="learn"
                )

        return JsonResponse({"message": "Profile updated"})

    return JsonResponse({"error": "POST only"}, status=400)

    
def get_user(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)

        return JsonResponse({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email
        })
    except:
        return JsonResponse({"error": "User not found"})
    

@csrf_exempt
def save_calendar_slots(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            username = data.get('username')
            slots = data.get('slots')

            from decouple import config
            from pymongo import MongoClient

            client = MongoClient(config("MONGO_URL"))
            db = client["swaplearn_database_final"]
            collection = db["availability"]

            collection.delete_many({"username": username})

            for slot in slots:
                collection.insert_one({
                    "username": username,
                    "day": slot["day"],
                    "time": slot["time"]
                })

            return JsonResponse({"message": "Saved successfully"})

        except Exception as e:
            print("ERROR:", str(e))
            return JsonResponse({"error": "Failed"}, status=500)

@csrf_exempt
def get_calendar_slots(request):
    username = request.GET.get('username')

    from decouple import config
    from pymongo import MongoClient

    client = MongoClient(config("MONGO_URL"))
    db = client["swaplearn_database_final"]
    collection = db["availability"]

    data = list(collection.find({"username": username}, {"_id": 0}))

    return JsonResponse(data, safe=False)

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import UserProfile

@csrf_exempt
def end_session(request):
    if request.method == "POST":
        data = json.loads(request.body)

        teacher_id = data.get("teacher_id")
        learner_id = data.get("learner_id")

        try:
            with transaction.atomic():

                teacher_profile = UserProfile.objects.get(
                    user__user_id=teacher_id
                )

                learner_profile = UserProfile.objects.get(
                    user__user_id=learner_id
                )

                if learner_profile.credit < 3:
                    return JsonResponse({"error": "Not enough credits"}, status=400)

                teacher_profile.credit += 2
                learner_profile.credit -= 3

                # Optional counters
                teacher_profile.skills_teach_count += 1
                learner_profile.skills_learn_count += 1

                teacher_profile.save()
                learner_profile.save()

            return JsonResponse({
                "message": "Credits updated",
                "teacher_credit": teacher_profile.credit,
                "learner_credit": learner_profile.credit,
                "teacher_taught_count": teacher_profile.skills_teach_count,
                "learner_learned_count": learner_profile.skills_learn_count
            })

        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "Profile not found"}, status=404)
        
def get_profile(request, user_id):

    try:

        profile = UserProfile.objects.get(
            user__user_id=user_id
        )

        return JsonResponse({

            "username": profile.username,

            "credit": profile.credit,

            "skills_learn_count":
                profile.skills_learn_count,

            "skills_teach_count":
                profile.skills_teach_count
        })

    except UserProfile.DoesNotExist:

        return JsonResponse({
            "error": "Profile not found"
        }, status=404)
    
@csrf_exempt
def accept_call(request):
    if request.method == "POST":
        data = json.loads(request.body)

        msg = Message.objects.get(message_id=data["message_id"])
        msg.status = "accepted"
        msg.save()

        return JsonResponse({"message": "call accepted"})
    
@csrf_exempt
def reject_call(request):
    if request.method == "POST":
        data = json.loads(request.body)

        msg = Message.objects.get(message_id=data["message_id"])
        msg.status = "rejected"
        msg.save()

        return JsonResponse({"message": "call rejected"})