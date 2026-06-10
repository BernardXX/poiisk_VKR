import re
from typing import List, Dict, Set

SKILL_ALIASES = {
    "python": ["python3", "python 3", "cpython"],
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts", "typescript 4", "typescript 5"],
    "vue.js": ["vue", "vuejs", "vue 2", "vue 3", "vue.js 3"],
    "react": ["react.js", "reactjs", "react 18"],
    "angular": ["angular 2+", "angularjs", "angular 14"],
    "node.js": ["nodejs", "node", "express.js", "express"],
    "django": ["django rest framework", "drf", "django 4"],
    "fastapi": ["fast api"],
    "flask": ["flask-restful"],
    "postgresql": ["postgres", "psql"],
    "mongodb": ["mongo", "mongoose"],
    "redis": ["redis cache"],
    "docker": ["docker container", "dockerize"],
    "git": ["github", "gitlab", "bitbucket"],
    "ci/cd": ["cicd", "continuous integration", "continuous deployment"],
    "rest api": ["rest", "restful", "http api"],
    "graphql": ["graph ql"],
    "aws": ["amazon web services", "ec2", "s3", "lambda"],
    "azure": ["microsoft azure"],
    "gcp": ["google cloud", "google cloud platform"],
    "linux": ["ubuntu", "centos", "debian", "bash", "shell"],
    "html": ["html5"],
    "css": ["css3", "scss", "sass", "less"],
    "webpack": ["webpack 5"],
    "jest": ["jest testing"],
    "pytest": ["py.test"],
    "selenium": ["selenium webdriver"],
    "terraform": ["tf", "infra as code"],
    "elasticsearch": ["elastic search", "elk"],
    "rabbitmq": ["rabbit mq", "amqp"],
    "kafka": ["apache kafka"],
    "apache": ["httpd"],
}

ALIAS_TO_CANONICAL = {}
for canonical, aliases in SKILL_ALIASES.items():
    ALIAS_TO_CANONICAL[canonical.lower()] = canonical.lower()
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias.lower()] = canonical.lower()

ALL_KNOWN_SKILLS = set(SKILL_ALIASES.keys())
for aliases in SKILL_ALIASES.values():
    ALL_KNOWN_SKILLS.update(aliases)


def normalize_skill(skill: str) -> str:
    """Приводит навык к каноническому виду"""
    skill_lower = skill.lower().strip()
    return ALIAS_TO_CANONICAL.get(skill_lower, skill_lower)


def extract_skills_from_text(text: str) -> Set[str]:
    """
    Извлекает известные технические навыки из текста вакансии
    Использует поиск по слову с учётом границ (чтобы 'cat' не матчился в 'catalog')
    """
    if not text:
        return set()
    
    text_lower = text.lower()
    found_skills = set()
    
    for skill in ALL_KNOWN_SKILLS:
        if '/' in skill or ' ' in skill:
            if skill in text_lower:
                found_skills.add(normalize_skill(skill))
        else:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(normalize_skill(skill))
    
    return found_skills