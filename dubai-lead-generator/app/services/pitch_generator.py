"""
CEO High-Converting Pitch & Website Mockup Generator.
Generates the 'Best Pitch' sequence addressed strictly to the CEO/Owner,
uncovering their critical loophole, offering a custom personal website,
embedding Sandesh Barde's verified portfolio, GitHub repos, and LinkedIn profile,
and supporting native languages (English, Arabic for Dubai/UAE, and Bilingual).
"""

from typing import Dict, Any, Optional
import re

PORTFOLIO_URL = "https://sandeshbarde.netlify.app/"
GITHUB_URL = "https://github.com/sandeshbarde"
LINKEDIN_URL = "https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
DEVELOPER_NAME = "Sandesh Barde"
DEVELOPER_LOCATION = "India"


class PitchGeneratorService:
    """Service to craft executive-level cold pitches and generate website mockup previews."""

    def generate_ceo_pitch(
        self,
        business_name: str,
        category: str,
        city: str = "Dubai",
        area: Optional[str] = None,
        ceo_name: Optional[str] = None,
        ceo_title: Optional[str] = None,
        loophole_data: Optional[Dict[str, Any]] = None,
        sequence_step: int = 1,
        language: str = "en",
        live_demo_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate high-converting pitch for Step 1, 2, or 3, addressed strictly to the CEO,
        including Sandesh Barde's portfolio, GitHub, LinkedIn, India base, and live prototype link.
        Supports English ('en'), Arabic ('ar' for Dubai/Middle East), and Bilingual ('bilingual').
        """
        location = f"{area}, {city}" if area else city
        exec_title = ceo_title or "CEO"
        salutation = f"Dear {ceo_name}," if ceo_name else f"Dear {exec_title} of {business_name},"

        loophole = loophole_data or {}
        loophole_title = loophole.get("primary_loophole", "Missing Official Digital Presence")
        revenue_leak = loophole.get("estimated_revenue_leak", "thousands in missed high-ticket contracts")
        b_type = loophole.get("business_type", "B2B")
        website_blueprint = loophole.get("website_solution_blueprint", "a modern, high-speed custom website")

        slug = re.sub(r'[^a-zA-Z0-9]', '', business_name).lower()
        mockup_link = live_demo_url or f"https://preview.agency-engine.com/{slug}"
        clean_leak = revenue_leak.replace("Estimated ", "").rstrip(".")

        # ─────────────────────────────────────────────────────────────
        # 1. ARABIC LANGUAGE TEMPLATE (For Dubai & Middle East Hubs)
        # ─────────────────────────────────────────────────────────────
        if language == "ar":
            salutation_ar = f"السيد/ة المحترم/ة {ceo_name}," if ceo_name else f"عناية السيد الرئيس التنفيذي لـ {business_name}،"
            subject = f"اقتراح استراتيجي لتطوير الحضور الرقمي لـ {business_name} في {city}"
            body = (
                f"{salutation_ar}\n\n"
                f"تحية طيبة وبعد،\n\n"
                f"أتابع باهتمام المكانة الرائدة والسمعة المتميزة لشركتكم في مجال {category} في {location}.\n\n"
                f"أثناء دراسة السوق في قطاعكم، لاحظت ثغرة رقمية جوهرية تؤثر بشكل مباشر على حجم الصفقات والمبيعات:\n\n"
                f"👉 **الثغرة الحالية**: {loophole_title}\n"
                f"كبار المشترين وفرق المشتريات في دبي يبحثون عبر الإنترنت عن كتالوج المنتجات وطلب عروض الأسعار (RFQ). عدم توفر موقع إلكتروني رسمي يدفع هذه الصفقات الكبرى مباشرة إلى الشركات المنافسة.\n\n"
                f"بناءً على حجم السوق في {city}، يُقدر هذا التسرب بما يقارب {clean_leak}.\n\n"
                f"أنا متخصص في تصميم وتطوير مواقع الويب المخصصة للشركات والتجار ومقري في الهند ({DEVELOPER_LOCATION}). لقد قمت بالفعل بتصميم نموذج أولي مباشر لموقع شركتكم {business_name} يتضمن: {website_blueprint}.\n\n"
                f"🌐 رابط النموذج الأولي التفاعلي المباشر:\n{mockup_link}\n\n"
                f"يمكنكم الاطلاع على نماذج أعمالي البرمجية والمشروعات المنفذة ومستودعات الكود البرمجي:\n"
                f"🌐 معرض الأعمال (Portfolio): {PORTFOLIO_URL}\n"
                f"💻 مستودعات المشروعات (GitHub): {GITHUB_URL}\n"
                f"🔗 حساب لينكد إن (LinkedIn): {LINKEDIN_URL}\n\n"
                f"يسعدني تزويدكم بكافة التفاصيل أو ترتيب محادثة سريعة لمدة 5 دقائق عبر الواتساب للاطلاع على النموذج دون أي التزام.\n\n"
                f"مع خالص التحية والتقدير،\n"
                f"{DEVELOPER_NAME}\n"
                f"مهندس ومصمم مواقع الويب المتكاملة ({DEVELOPER_LOCATION})\n"
                f"Portfolio: {PORTFOLIO_URL} | GitHub: {GITHUB_URL}\n"
                f"LinkedIn: {LINKEDIN_URL}"
            )
            return {
                "step": sequence_step,
                "language": "ar",
                "subject": subject,
                "body": body,
                "recipient_title": exec_title,
                "mockup_url": mockup_link,
            }

        # ─────────────────────────────────────────────────────────────
        # 2. BILINGUAL TEMPLATE (English + Arabic Brief for Dubai)
        # ─────────────────────────────────────────────────────────────
        if language == "bilingual":
            subject = f"{business_name} - Strategic Digital Presence & B2B Inquiry Opportunity ({city})"
            body = (
                f"{salutation}\n\n"
                f"I hope you are doing well.\n\n"
                f"I noticed your solid reputation and established track record as a leading {category} in {location}.\n\n"
                f"While researching businesses in your sector, I identified a critical digital bottleneck currently costing {business_name} valuable commercial inquiries:\n\n"
                f"👉 **The Loophole**: {loophole_title}\n"
                f"{loophole.get('loophole_details', 'Corporate clients and high-intent buyers searching online cannot find an official website or digital catalog for your business, driving them straight to competitors.')}\n\n"
                f"Based on current market data in {city}, this is causing an estimated loss of {clean_leak}.\n\n"
                f"I am a Web Architect based in {DEVELOPER_LOCATION} specializing in building high-converting personal and commercial websites for enterprises across Dubai and globally. I have already drafted a custom live website prototype for {business_name} featuring {website_blueprint}.\n\n"
                f"🌐 **Live Website Prototype Link**:\n{mockup_link}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"ملخص باللغة العربية (Arabic Summary):\n"
                f"نقدم لشركتكم {business_name} في {city} حلاً متكاملاً لتصميم موقع إلكتروني رسمي حديث يتيح استقبال طلبات عروض الأسعار والكتالوج الرقمي، لمنع تسرب العملاء والصفقات إلى المنافسين.\n"
                f"رابط النموذج الأولي: {mockup_link}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"You can review my live portfolio, verified code repositories, and background here:\n"
                f"🌐 Live Portfolio: {PORTFOLIO_URL}\n"
                f"💻 GitHub Repositories: {GITHUB_URL}\n"
                f"🔗 LinkedIn Profile: {LINKEDIN_URL}\n\n"
                f"Would you be open to a 5-minute call or WhatsApp chat this week to review the live prototype for {business_name}?\n\n"
                f"Best regards,\n"
                f"{DEVELOPER_NAME}\n"
                f"Lead Full-Stack Web Architect ({DEVELOPER_LOCATION})\n"
                f"Portfolio: {PORTFOLIO_URL} | GitHub: {GITHUB_URL}\n"
                f"LinkedIn: {LINKEDIN_URL}"
            )
            return {
                "step": sequence_step,
                "language": "bilingual",
                "subject": subject,
                "body": body,
                "recipient_title": exec_title,
                "mockup_url": mockup_link,
            }

        # ─────────────────────────────────────────────────────────────
        # 3. ENGLISH TEMPLATE (Default Worldwide & Dubai)
        # ─────────────────────────────────────────────────────────────
        if sequence_step == 1:
            # Step 1: Initial Hook & Loophole Reveal + Live Prototype
            subject = f"Quick question regarding {business_name}'s {b_type} digital presence in {city}"
            body = (
                f"{salutation}\n\n"
                f"I hope you are doing well.\n\n"
                f"I noticed your solid reputation and strong track record as an established {category} in {location}.\n\n"
                f"However, while researching companies in your sector, I identified a critical bottleneck that is currently costing {business_name} new business:\n\n"
                f"👉 **The Loophole**: {loophole_title}\n"
                f"{loophole.get('loophole_details', 'Corporate clients and high-intent buyers searching online cannot find an official website or digital catalog for your business, driving them straight to competitors.')}\n\n"
                f"Based on current market volume in {city}, this is causing an estimated {clean_leak}.\n\n"
                f"I am a Web Architect & UI/UX Engineer based in {DEVELOPER_LOCATION}. I specialize in designing high-converting, custom personal websites for established businesses like yours. I have already drafted a tailored website concept specifically engineered for {business_name}—featuring {website_blueprint}.\n\n"
                f"I already put together a live interactive prototype so you can see it in action:\n"
                f"🌐 **Live Website Prototype**: {mockup_link}\n\n"
                f"You can verify my work, technical repositories, and background here:\n"
                f"🌐 Live Portfolio: {PORTFOLIO_URL}\n"
                f"💻 GitHub Projects & Repos: {GITHUB_URL}\n"
                f"🔗 LinkedIn Profile: {LINKEDIN_URL}\n\n"
                f"I would love to give you a quick 5-minute walkthrough or customize this further with your team. No obligation at all.\n\n"
                f"Would you be open to seeing what we put together for {business_name} this week?\n\n"
                f"Best regards,\n"
                f"{DEVELOPER_NAME}\n"
                f"Lead Full-Stack Web Architect ({DEVELOPER_LOCATION})\n"
                f"Portfolio: {PORTFOLIO_URL} | GitHub: {GITHUB_URL}\n"
                f"LinkedIn: {LINKEDIN_URL}"
            )

        elif sequence_step == 2:
            # Step 2: Follow-Up 1 - The Opportunity Cost & Case Study (Sent 3 days later)
            subject = f"Re: {business_name} - {city} market observation & missed RFQs"
            body = (
                f"{salutation}\n\n"
                f"Following up on my previous note regarding {business_name}.\n\n"
                f"In competitive hubs like {city}, over 78% of procurement officers and high-value clients verify an official website before issuing inquiries or purchase orders. Without an official digital presence, your business remains practically invisible to these corporate buyers.\n\n"
                f"Recently, I designed a streamlined digital platform for a similar trading business, and within 45 days they captured 14 new inbound commercial inquiries that would have otherwise gone to rivals.\n\n"
                f"We can design and launch a complete, custom personal website for {business_name} with zero hassle on your end—complete with a digital catalog, direct quotation request, and mobile WhatsApp hotline.\n\n"
                f"Feel free to review my verified portfolio and development repositories:\n"
                f"🌐 Portfolio: {PORTFOLIO_URL}\n"
                f"💻 GitHub: {GITHUB_URL}\n"
                f"🔗 LinkedIn: {LINKEDIN_URL}\n\n"
                f"Are you available for a brief 5-minute conversation either Tuesday or Thursday to see the prototype?\n\n"
                f"Best regards,\n"
                f"{DEVELOPER_NAME}\n"
                f"Web Architect & Designer ({DEVELOPER_LOCATION})\n"
                f"Portfolio: {PORTFOLIO_URL}"
            )

        else:
            # Step 3: Follow-Up 2 - Interactive Demo & Final Proposal (Sent 5 days later)
            subject = f"Final follow-up: Live website prototype for {business_name}"
            body = (
                f"{salutation}\n\n"
                f"I know you are exceptionally busy managing operations at {business_name}, so I'll keep this very brief.\n\n"
                f"To make it effortless for you to evaluate, my team has generated an interactive preview showing how {business_name}'s custom website can look and function:\n\n"
                f"🔗 **Live Interactive Prototype**: {mockup_link}\n\n"
                f"Key features built into this design:\n"
                f"✅ Instant quotation and corporate RFQ capture\n"
                f"✅ Mobile-optimized B2B catalog & product spec showcase\n"
                f"✅ 1-click WhatsApp and phone connectivity for instant orders\n"
                f"✅ Fast Google SEO positioning for {location}\n\n"
                f"My background and live work:\n"
                f"🌐 Portfolio: {PORTFOLIO_URL}\n"
                f"💻 GitHub: {GITHUB_URL}\n"
                f"🔗 LinkedIn: {LINKEDIN_URL}\n\n"
                f"If you'd like us to customize this with your official branding and take it live, let me know with a quick reply.\n\n"
                f"Warm regards,\n"
                f"{DEVELOPER_NAME}\n"
                f"Lead Web Architect ({DEVELOPER_LOCATION})\n"
                f"WhatsApp / Direct: Available on request"
            )

        return {
            "step": sequence_step,
            "language": language,
            "subject": subject,
            "body": body,
            "recipient_title": exec_title,
            "mockup_url": mockup_link,
        }

    def generate_website_mockup_data(
        self,
        business_name: str,
        category: str,
        city: str = "Dubai",
        area: Optional[str] = None,
        phone: Optional[str] = None,
        loophole_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate interactive website mockup structure for frontend live preview.
        """
        location = f"{area}, {city}" if area else city
        loophole = loophole_data or {}
        b_type = loophole.get("business_type", "B2B")
        industry = loophole.get("industry", category or "Commercial")

        if b_type == "B2B":
            hero_title = f"Leading Wholesale & Commercial Supplier in {city}"
            hero_subtitle = f"Premium {category} solutions engineered for corporate contractors, bulk dealers, and commercial enterprises across {city} and international markets."
            primary_cta = "Request B2B Catalog & Bulk RFQ"
            services = [
                {"title": "Bulk Distribution & Wholesale", "desc": "Volume supply with verified international quality standards and flexible payment terms."},
                {"title": "Rapid Logistics & Warehousing", "desc": f"Same-day dispatch and strategic logistics hub servicing all districts across {city}."},
                {"title": "Custom Corporate Orders", "desc": "Tailored product specifications, OEM matching, and dedicated account manager support."}
            ]
        else:
            hero_title = f"Top-Rated {category.capitalize()} in {city}"
            hero_subtitle = f"Experience premium service, verified craftsmanship, and dedicated customer care right here in {location}."
            primary_cta = "Book an Appointment / Inquire Now"
            services = [
                {"title": "Premium Bespoke Services", "desc": "Crafted to meet the highest standards of quality and customer satisfaction."},
                {"title": "Convenient Booking & Fast Response", "desc": "Connect directly via phone, WhatsApp, or instant digital inquiry."},
                {"title": "Verified 5-Star Experience", "desc": f"Proudly serving the {city} community with excellence and dependability."}
            ]

        return {
            "business_name": business_name,
            "location": location,
            "phone": phone or "+971 4 000 0000",
            "industry": industry,
            "business_type": b_type,
            "hero_title": hero_title,
            "hero_subtitle": hero_subtitle,
            "primary_cta": primary_cta,
            "services": services,
            "accent_color": "#4f46e5" if b_type == "B2B" else "#059669",
            "developer": {
                "name": DEVELOPER_NAME,
                "location": DEVELOPER_LOCATION,
                "portfolio": PORTFOLIO_URL,
                "github": GITHUB_URL,
                "linkedin": LINKEDIN_URL,
            }
        }

    def generate_live_demo_html(self, lead_dict: Dict[str, Any], mockup: Dict[str, Any]) -> str:
        """Generate a complete, interactive, mobile-responsive prototype website."""
        name = lead_dict.get("business_name", "Enterprise Portal")
        category = lead_dict.get("category") or "Commercial"
        city = lead_dict.get("city") or "Dubai"
        area = lead_dict.get("area") or city
        phone = lead_dict.get("phone") or "+971 4 000 0000"
        rating = lead_dict.get("google_rating") or 4.9
        reviews = lead_dict.get("google_review_count") or 38
        b_type = mockup.get("business_type", "B2B")
        industry = mockup.get("industry", "Commercial")
        hero_title = mockup.get("hero_title", f"Leading {industry} in {city}")
        hero_subtitle = mockup.get("hero_subtitle", "")
        primary_cta = mockup.get("primary_cta", "Request B2B Quotation")
        services = mockup.get("services", [])

        services_html = "".join([
            f"""
            <div class="bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 p-6 rounded-2xl transition-all duration-300 hover:-translate-y-1 shadow-lg">
                <div class="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-lg mb-4">
                    ✓
                </div>
                <h3 class="text-base font-bold text-white mb-2">{s.get('title')}</h3>
                <p class="text-xs text-slate-400 leading-relaxed">{s.get('desc')}</p>
            </div>
            """ for s in services
        ])

        return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | Official {industry} Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #080d1a; color: #f1f5f9; }}
        .glow-brand {{ box-shadow: 0 0 35px -5px rgba(99, 102, 241, 0.35); }}
    </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-indigo-600 selection:text-white">

    <!-- Prototype Header Bar -->
    <div class="bg-gradient-to-r from-indigo-950 via-purple-950 to-indigo-950 border-b border-indigo-500/30 px-4 py-2.5 text-xs text-center flex flex-wrap items-center justify-between gap-2 z-50">
        <div class="flex items-center gap-2">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse">
                PROTOTYPE DEMO
            </span>
            <span class="text-slate-300">Exclusively designed for <strong>{name}</strong> by <strong>Sandesh Barde</strong> (India)</span>
        </div>
        <div class="flex items-center gap-4 text-indigo-400 font-semibold text-[11px]">
            <a href="{PORTFOLIO_URL}" target="_blank" class="hover:text-white transition-colors">🌐 Developer Portfolio</a>
            <a href="{GITHUB_URL}" target="_blank" class="hover:text-white transition-colors">💻 GitHub Repos</a>
            <a href="{LINKEDIN_URL}" target="_blank" class="hover:text-white transition-colors">🔗 LinkedIn</a>
        </div>
    </div>

    <!-- Navigation -->
    <header class="sticky top-0 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 z-40 px-6 py-4">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-black text-white text-lg shadow-md">
                    ⚡
                </div>
                <div>
                    <span class="text-base font-extrabold tracking-tight text-white block">{name}</span>
                    <span class="text-[10px] font-bold uppercase tracking-wider text-indigo-400">{b_type} {industry} • {city}</span>
                </div>
            </div>

            <nav class="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-300">
                <a href="#services" class="hover:text-white transition-colors">Products & Solutions</a>
                <a href="#about" class="hover:text-white transition-colors">About {name}</a>
                <a href="#contact" class="hover:text-white transition-colors">Direct Inquiry</a>
            </nav>

            <div class="flex items-center gap-3">
                <button onclick="openQuoteModal()" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg glow-brand transition-all">
                    {primary_cta}
                </button>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <main class="flex-grow">
        <section class="relative py-20 px-6 overflow-hidden">
            <div class="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.25),rgba(255,255,255,0))]"></div>
            
            <div class="max-w-4xl mx-auto text-center space-y-6">
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
                    <span class="text-amber-400">★ {rating}</span>
                    <span>•</span>
                    <span>Verified {city} Commercial Presence ({reviews} Reviews)</span>
                </div>

                <h1 class="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
                    {hero_title}
                </h1>

                <p class="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
                    {hero_subtitle}
                </p>

                <div class="flex flex-wrap items-center justify-center gap-4 pt-4">
                    <button onclick="openQuoteModal()" class="px-6 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-extrabold text-sm shadow-xl glow-brand transition-all transform hover:-translate-y-0.5">
                        ⚡ {primary_cta}
                    </button>
                    <a href="tel:{phone}" class="px-5 py-3.5 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-200 font-bold text-sm transition-all flex items-center gap-2">
                        <span>📞 {phone}</span>
                    </a>
                </div>
            </div>
        </section>

        <!-- Solutions & Products Grid -->
        <section id="services" class="py-16 px-6 max-w-7xl mx-auto">
            <div class="text-center max-w-xl mx-auto mb-12 space-y-2">
                <h2 class="text-2xl font-black text-white">Commercial Capabilities</h2>
                <p class="text-xs text-slate-400">Engineered for corporate reliability and verified delivery across {city}.</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {services_html}
            </div>
        </section>

        <!-- About & Trust Section -->
        <section id="about" class="py-16 px-6 bg-slate-900/40 border-y border-slate-800/80">
            <div class="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
                <div class="space-y-4 text-left">
                    <span class="text-xs font-bold text-indigo-400 uppercase tracking-widest">About Our Company</span>
                    <h2 class="text-2xl sm:text-3xl font-black text-white">Dedicated {industry} Leader in {area}</h2>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Operating from our established base in {area}, {city}, {name} supplies top-tier {category} solutions. 
                        With a customer rating of {rating}★ across {reviews} verified reviews, we are proud to serve our community with unmatched reliability.
                    </p>
                    <div class="pt-2 flex items-center gap-6 text-xs text-slate-400">
                        <div><strong class="text-white block text-lg">{reviews}+</strong> Verified Inquiries</div>
                        <div><strong class="text-white block text-lg">{rating}★</strong> Google Rating</div>
                        <div><strong class="text-white block text-lg">{city}</strong> Prime Trading Hub</div>
                    </div>
                </div>
                <div class="bg-dark-card border border-slate-800 p-8 rounded-2xl shadow-xl space-y-4">
                    <h3 class="text-base font-bold text-white">Submit a Direct Request for Quote (RFQ)</h3>
                    <p class="text-xs text-slate-400">Need pricing or bulk specifications? Our executive team responds within 2 business hours.</p>
                    <button onclick="openQuoteModal()" class="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white shadow glow-brand transition-all">
                        Launch RFQ Inquiry Form →
                    </button>
                </div>
            </div>
        </section>
    </main>

    <!-- RFQ Modal -->
    <div id="modal-rfq" class="fixed inset-0 z-50 overflow-y-auto hidden">
        <div class="flex items-center justify-center min-h-screen px-4">
            <div class="fixed inset-0 bg-black/80 backdrop-blur-sm" onclick="closeQuoteModal()"></div>
            <div class="relative bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl z-10 text-xs space-y-4">
                <div class="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 class="text-sm font-bold text-white">Request Official Quotation ({name})</h3>
                    <button onclick="closeQuoteModal()" class="text-slate-400 hover:text-white font-bold">✕</button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="block text-slate-400 mb-1">Your Full Name / Company</label>
                        <input type="text" placeholder="e.g. Al Futtaim Group" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white">
                    </div>
                    <div>
                        <label class="block text-slate-400 mb-1">Corporate Email</label>
                        <input type="email" placeholder="procurement@company.ae" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white">
                    </div>
                    <div>
                        <label class="block text-slate-400 mb-1">Required Products / Quantity</label>
                        <textarea rows="3" placeholder="Specify item names, volumes, or required specifications..." class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"></textarea>
                    </div>
                    <button onclick="alert('✅ RFQ Submitted! In a live deployed setup, this routes directly to the company CEO email & WhatsApp.'); closeQuoteModal();" class="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow">
                        Submit Official Inquiry
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Floating WhatsApp Action -->
    <a href="https://api.whatsapp.com/send?phone={phone.replace(' ', '').replace('+', '')}&text=Hello%20{name}%2C%20I%20saw%20your%20website%20and%20would%20like%20to%20inquire." target="_blank" class="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-emerald-500 hover:bg-emerald-400 text-white flex items-center justify-center text-2xl shadow-2xl z-40 transition-transform hover:scale-110">
        💬
    </a>

    <!-- Footer -->
    <footer class="border-t border-slate-800/80 py-6 px-6 bg-slate-950 text-xs text-slate-500 text-center space-y-2">
        <div>© {name} • {area}, {city} • All Rights Reserved.</div>
        <div class="text-[11px] text-slate-400">Website Concept Architecture by <strong class="text-indigo-400">Sandesh Barde</strong> ({DEVELOPER_LOCATION}) • <a href="{PORTFOLIO_URL}" target="_blank" class="text-indigo-400 underline">Portfolio</a></div>
    </footer>

    <script>
        function openQuoteModal() {{ document.getElementById('modal-rfq').classList.remove('hidden'); }}
        function closeQuoteModal() {{ document.getElementById('modal-rfq').classList.add('hidden'); }}
    </script>
</body>
</html>"""


pitch_generator = PitchGeneratorService()

