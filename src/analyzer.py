def analyze_skills(resume_skills, job_skills):

    resume_set = set(resume_skills)
    job_set = set(job_skills)

    matched = sorted(resume_set.intersection(job_set))
    missing = sorted(job_set - resume_set)

    if job_set:
        skill_score = round(
            (len(matched) / len(job_set)) * 100,
            2
        )
    else:
        skill_score = 0

    return matched, missing, skill_score
