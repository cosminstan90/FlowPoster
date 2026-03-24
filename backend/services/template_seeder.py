"""
Seeds the prompt_templates table with 3 default templates on first startup.
Called from the FastAPI lifespan event when the table is empty.
"""
from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)

_DEFAULTS = [
    {
        "name": "Article RO",
        "type": "article",
        "variables": ["keyword", "site_context", "outline", "author_context", "internal_links_context"],
        "system_prompt": (
            "Ești un copywriter SEO senior. Scrie ÎNTOTDEAUNA în limba română. "
            "Stilul este informativ, clar și util cititorului. "
            "Articolul trebuie să aibă minim 700 de cuvinte. "
            "Folosește taguri HTML semantice: h2, h3, p, ul, ol, strong, em. "
            "NU folosi markdown. "
            "Răspunde EXCLUSIV cu un obiect JSON valid cu cheile: "
            "title, slug, meta_description, content_html, faq_items, schema_markup."
        ),
        "user_prompt": (
            "Scrie un articol SEO complet pentru keyword-ul: {keyword}\n\n"
            "Context site:\n{site_context}\n\n"
            "Outline de urmat:\n{outline}\n\n"
            "Context autor:\n{author_context}\n\n"
            "Pagini interne disponibile pentru link-uri:\n{internal_links_context}\n\n"
            "Cerințe:\n"
            "- Minim 700 de cuvinte\n"
            "- Secțiune FAQ cu 5+ întrebări și răspunsuri\n"
            "- Schema markup de tip Article + FAQPage\n"
            "- Meta description între 120-155 caractere\n\n"
            "Returnează JSON cu cheile: title, slug, meta_description, content_html, "
            "faq_items (array de {question, answer}), schema_markup."
        ),
    },
    {
        "name": "Article EN",
        "type": "article",
        "variables": ["keyword", "site_context", "outline", "author_context", "internal_links_context"],
        "system_prompt": (
            "You are a senior SEO copywriter. Write EXCLUSIVELY in English. "
            "The style is informative, clear, and reader-focused. "
            "The article must be at least 700 words. "
            "Use semantic HTML tags: h2, h3, p, ul, ol, strong, em. "
            "Do NOT use markdown. "
            "Respond ONLY with a valid JSON object with keys: "
            "title, slug, meta_description, content_html, faq_items, schema_markup."
        ),
        "user_prompt": (
            "Write a complete SEO article for the keyword: {keyword}\n\n"
            "Site context:\n{site_context}\n\n"
            "Outline to follow:\n{outline}\n\n"
            "Author context:\n{author_context}\n\n"
            "Internal pages available for linking:\n{internal_links_context}\n\n"
            "Requirements:\n"
            "- At least 700 words\n"
            "- FAQ section with 5+ questions and answers\n"
            "- Article + FAQPage schema markup\n"
            "- Meta description 120-155 characters\n\n"
            "Return JSON with keys: title, slug, meta_description, content_html, "
            "faq_items (array of {question, answer}), schema_markup."
        ),
    },
    {
        "name": "FAQ Page RO",
        "type": "faq",
        "variables": ["keyword", "site_context", "outline", "author_context"],
        "system_prompt": (
            "Ești un specialist în pagini FAQ și conținut structurat. "
            "Scrie ÎNTOTDEAUNA în limba română. "
            "Paginile FAQ trebuie să aibă minimum 10 întrebări cu răspunsuri clare și detaliate. "
            "Dacă keyword-ul implică un proces sau instrucțiuni, adaugă schema HowTo. "
            "Folosește taguri HTML semantice și structură clară. "
            "Răspunde EXCLUSIV cu un obiect JSON valid cu cheile: "
            "title, slug, meta_description, content_html, faq_items, schema_markup."
        ),
        "user_prompt": (
            "Creează o pagină FAQ completă pentru keyword-ul: {keyword}\n\n"
            "Context site:\n{site_context}\n\n"
            "Structură sugerată:\n{outline}\n\n"
            "Context autor:\n{author_context}\n\n"
            "Cerințe:\n"
            "- Minimum 10 întrebări cu răspunsuri detaliate (2-4 propoziții fiecare)\n"
            "- Intro de 100-150 cuvinte înainte de FAQ\n"
            "- Schema FAQPage (și HowTo dacă se aplică)\n"
            "- Meta description între 120-155 caractere\n\n"
            "Returnează JSON cu cheile: title, slug, meta_description, content_html, "
            "faq_items (array de {question, answer}), schema_markup."
        ),
    },
]


async def seed_default_templates(db: AsyncSession) -> None:
    count = await db.scalar(select(func.count(PromptTemplate.id)))
    if count and count > 0:
        return

    logger.info("Seeding %d default prompt templates", len(_DEFAULTS))
    for data in _DEFAULTS:
        db.add(PromptTemplate(**data))
    await db.commit()
    logger.info("Default templates seeded")
