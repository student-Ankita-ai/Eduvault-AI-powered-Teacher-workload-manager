def parse_teacher_voice_command(command_text):
    text = command_text.lower()
    if "rahul" in text:
        return {"roll_no": 101, "doc_type": "income", "entity": "Rahul Kumar (Roll No. 101)"}
    elif "priya" in text:
        return {"roll_no": 102, "doc_type": "bank", "entity": "Priya Sharma (Roll No. 102)"}
    else:
        return {"roll_no": 101, "doc_type": "income", "entity": "Rahul Kumar (Roll No. 101)"}