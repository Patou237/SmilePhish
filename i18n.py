"""
Internationalisation (i18n) de SmilePhish.
Langues disponibles : français (fr, par défaut), anglais (en), allemand (de),
espagnol (es), chinois simplifié (zh).

Usage côté templates : {{ t('nav_history') }}
Usage côté Python : from i18n import t ; t('nav_history', lang='en')
"""

LANGUAGES = {
    "fr": "Français",
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "zh": "中文",
}

DEFAULT_LANG = "fr"

TRANSLATIONS = {
    # ---------------------------------------------------------------- Navbar
    "brand_tagline": {
        "fr": "Simulation & sensibilisation phishing",
        "en": "Phishing simulation & awareness",
        "de": "Phishing-Simulation & Sensibilisierung",
        "es": "Simulación y concienciación sobre phishing",
        "zh": "钓鱼模拟与安全意识培训",
    },
    "nav_history": {
        "fr": "Historique des campagnes", "en": "Campaign history",
        "de": "Kampagnenverlauf", "es": "Historial de campañas", "zh": "活动历史",
    },
    "nav_new_campaign": {
        "fr": "+ Nouvelle campagne", "en": "+ New campaign",
        "de": "+ Neue Kampagne", "es": "+ Nueva campaña", "zh": "+ 新建活动",
    },
    "nav_schedules": {
        "fr": "Planifications", "en": "Scheduled sends",
        "de": "Planungen", "es": "Programaciones", "zh": "计划任务",
    },
    "nav_account": {
        "fr": "Mon compte", "en": "My account",
        "de": "Mein Konto", "es": "Mi cuenta", "zh": "我的账户",
    },
    "nav_logout": {
        "fr": "Déconnexion", "en": "Log out",
        "de": "Abmelden", "es": "Cerrar sesión", "zh": "退出登录",
    },
    "nav_support": {
        "fr": "Assistance", "en": "Support", "de": "Support", "es": "Soporte", "zh": "支持",
    },
    "nav_audit": {
        "fr": "Journal des connexions", "en": "Login audit", "de": "Anmeldeprotokoll",
        "es": "Registro de accesos", "zh": "登录审计",
    },
    "nav_superadmin": {
        "fr": "Super-admin", "en": "Super admin", "de": "Super-Admin", "es": "Superadmin", "zh": "超级管理员",
    },
    "nav_terms": {
        "fr": "Conditions d'utilisation", "en": "Terms of use", "de": "Nutzungsbedingungen",
        "es": "Condiciones de uso", "zh": "使用条款",
    },
    "nav_login": {
        "fr": "Connexion", "en": "Log in", "de": "Anmelden", "es": "Iniciar sesión", "zh": "登录",
    },
    "nav_signup": {
        "fr": "Créer un compte", "en": "Sign up", "de": "Registrieren",
        "es": "Crear cuenta", "zh": "注册账户",
    },

    # ---------------------------------------------------------------- Auth
    "login_title": {
        "fr": "Connexion", "en": "Log in", "de": "Anmeldung", "es": "Iniciar sesión", "zh": "登录",
    },
    "signup_title": {
        "fr": "Créer votre compte SmilePhish", "en": "Create your SmilePhish account",
        "de": "SmilePhish-Konto erstellen", "es": "Crea tu cuenta SmilePhish", "zh": "创建 SmilePhish 账户",
    },
    "signup_sub": {
        "fr": "N'importe quelle adresse email fonctionne — aucune vérification de domaine requise.",
        "en": "Any email address works — no domain verification required.",
        "de": "Jede E-Mail-Adresse funktioniert — keine Domänenprüfung erforderlich.",
        "es": "Cualquier dirección de correo funciona — no se requiere verificación de dominio.",
        "zh": "任何邮箱地址均可注册，无需域名验证。",
    },
    "label_email": {"fr": "Adresse email", "en": "Email address", "de": "E-Mail-Adresse", "es": "Correo electrónico", "zh": "电子邮箱"},
    "label_password": {"fr": "Mot de passe", "en": "Password", "de": "Passwort", "es": "Contraseña", "zh": "密码"},
    "label_company": {
        "fr": "Nom de votre structure / cabinet", "en": "Your company / consultancy name",
        "de": "Name Ihres Unternehmens", "es": "Nombre de tu empresa", "zh": "公司/机构名称",
    },
    "btn_signup": {"fr": "Créer mon compte", "en": "Create my account", "de": "Konto erstellen", "es": "Crear cuenta", "zh": "创建账户"},
    "btn_login": {"fr": "Se connecter", "en": "Log in", "de": "Anmelden", "es": "Entrar", "zh": "登录"},
    "have_account": {"fr": "Déjà un compte ?", "en": "Already have an account?", "de": "Bereits registriert?", "es": "¿Ya tienes cuenta?", "zh": "已有账户？"},
    "no_account": {"fr": "Pas encore de compte ?", "en": "No account yet?", "de": "Noch kein Konto?", "es": "¿Aún no tienes cuenta?", "zh": "还没有账户？"},
    "err_login": {
        "fr": "Email ou mot de passe incorrect.", "en": "Incorrect email or password.",
        "de": "E-Mail oder Passwort falsch.", "es": "Correo o contraseña incorrectos.", "zh": "邮箱或密码错误。",
    },
    "err_email_taken": {
        "fr": "Un compte existe déjà avec cet email.", "en": "An account already exists with this email.",
        "de": "Für diese E-Mail existiert bereits ein Konto.", "es": "Ya existe una cuenta con este correo.", "zh": "该邮箱已被注册。",
    },
    "err_terms_required": {
        "fr": "Vous devez accepter les conditions d'utilisation pour créer un compte.",
        "en": "You must accept the terms of use to create an account.",
        "de": "Sie müssen die Nutzungsbedingungen akzeptieren, um ein Konto zu erstellen.",
        "es": "Debes aceptar las condiciones de uso para crear una cuenta.",
        "zh": "您必须接受使用条款才能创建账户。",
    },
    "err_traceability_required": {
        "fr": "Nom complet et objectif d'utilisation sont obligatoires (traçabilité en cas d'usage non éthique).",
        "en": "Full name and declared purpose are required (traceability in case of unethical use).",
        "de": "Vollständiger Name und Nutzungszweck sind erforderlich (Rückverfolgbarkeit bei unethischer Nutzung).",
        "es": "El nombre completo y el propósito declarado son obligatorios (trazabilidad en caso de uso no ético).",
        "zh": "必须填写全名和使用目的（用于不当使用时的追溯）。",
    },
    "err_license_invalid": {
        "fr": "Clé de licence invalide.", "en": "Invalid license key.",
        "de": "Ungültiger Lizenzschlüssel.", "es": "Clave de licencia no válida.", "zh": "许可证密钥无效。",
    },
    "err_license_revoked": {
        "fr": "Cette licence a été révoquée par l'administrateur de la plateforme.",
        "en": "This license has been revoked by the platform administrator.",
        "de": "Diese Lizenz wurde vom Plattformadministrator gesperrt.",
        "es": "Esta licencia ha sido revocada por el administrador de la plataforma.",
        "zh": "该许可证已被平台管理员撤销。",
    },
    "err_license_full": {
        "fr": "Cette licence a déjà atteint son nombre maximal de comptes (5).",
        "en": "This license has already reached its maximum number of accounts (5).",
        "de": "Diese Lizenz hat bereits die maximale Anzahl an Konten erreicht (5).",
        "es": "Esta licencia ya alcanzó su número máximo de cuentas (5).",
        "zh": "该许可证已达到最大账户数（5个）。",
    },

    # ---------------------------------------------------------------- Accueil / historique
    "history_title": {"fr": "Historique des campagnes", "en": "Campaign history", "de": "Kampagnenverlauf", "es": "Historial de campañas", "zh": "活动历史"},
    "history_sub": {
        "fr": "Toutes vos campagnes, classées par entreprise cliente, restent archivées ici.",
        "en": "All your campaigns, grouped by client organisation, stay archived here.",
        "de": "Alle Ihre Kampagnen, gruppiert nach Kundenunternehmen, bleiben hier archiviert.",
        "es": "Todas tus campañas, agrupadas por empresa cliente, quedan archivadas aquí.",
        "zh": "您的所有活动按客户组织归档保存在此。",
    },
    "no_campaigns": {
        "fr": "Aucune campagne pour l'instant. Cliquez sur \"+ Nouvelle campagne\" pour démarrer.",
        "en": "No campaigns yet. Click \"+ New campaign\" to get started.",
        "de": "Noch keine Kampagnen. Klicken Sie auf \"+ Neue Kampagne\", um zu starten.",
        "es": "Aún no hay campañas. Haz clic en \"+ Nueva campaña\" para empezar.",
        "zh": "暂无活动，点击“+ 新建活动”开始。",
    },
    "col_targets": {"fr": "Cibles", "en": "Targets", "de": "Ziele", "es": "Objetivos", "zh": "目标人数"},
    "col_sent": {"fr": "Envoyés", "en": "Sent", "de": "Gesendet", "es": "Enviados", "zh": "已发送"},
    "col_clicked": {"fr": "Cliqués", "en": "Clicked", "de": "Geklickt", "es": "Clics", "zh": "点击"},
    "col_click_rate": {"fr": "Taux clic", "en": "Click rate", "de": "Klickrate", "es": "Tasa de clics", "zh": "点击率"},
    "open_dashboard": {"fr": "Ouvrir", "en": "Open", "de": "Öffnen", "es": "Abrir", "zh": "打开"},

    # ---------------------------------------------------------------- Plan / quota
    "plan_free": {"fr": "Essai gratuit", "en": "Free trial", "de": "Kostenlose Testversion", "es": "Prueba gratuita", "zh": "免费试用"},
    "plan_pro": {"fr": "Pro", "en": "Pro", "de": "Pro", "es": "Pro", "zh": "专业版"},
    "quota_widget_free": {
        "fr": "Essai gratuit : {used}/{limit} emails envoyés (à vie)",
        "en": "Free trial: {used}/{limit} emails sent (lifetime)",
        "de": "Kostenlose Testversion: {used}/{limit} E-Mails gesendet (insgesamt)",
        "es": "Prueba gratuita: {used}/{limit} correos enviados (acumulado)",
        "zh": "免费试用：累计已发送 {used}/{limit} 封邮件",
    },
    "quota_widget_pro": {
        "fr": "Offre Pro : jusqu'à {limit} destinataires par envoi",
        "en": "Pro plan: up to {limit} recipients per send",
        "de": "Pro-Tarif: bis zu {limit} Empfänger pro Versand",
        "es": "Plan Pro: hasta {limit} destinatarios por envío",
        "zh": "专业版：每次最多可发送 {limit} 个收件人",
    },
    "btn_upgrade": {
        "fr": "Passer en Pro (1000 destinataires/envoi)", "en": "Upgrade to Pro (1000 recipients/send)",
        "de": "Auf Pro upgraden (1000 Empfänger/Versand)", "es": "Pasar a Pro (1000 destinatarios/envío)",
        "zh": "升级到专业版（每次1000个收件人）",
    },

    # ---------------------------------------------------------------- Nouvelle campagne
    "new_campaign_title": {"fr": "Nouvelle campagne", "en": "New campaign", "de": "Neue Kampagne", "es": "Nueva campaña", "zh": "新建活动"},
    "label_organisation": {
        "fr": "Entreprise cliente", "en": "Client organisation", "de": "Kundenunternehmen",
        "es": "Empresa cliente", "zh": "客户企业",
    },
    "organisation_new_hint": {
        "fr": "Choisissez une organisation existante ou tapez un nouveau nom pour en créer une.",
        "en": "Pick an existing organisation or type a new name to create one.",
        "de": "Wählen Sie eine bestehende Organisation oder geben Sie einen neuen Namen ein.",
        "es": "Elige una organización existente o escribe un nombre nuevo para crearla.",
        "zh": "选择已有企业，或输入新名称以创建。",
    },
    "label_campaign_name": {"fr": "Nom de la campagne", "en": "Campaign name", "de": "Kampagnenname", "es": "Nombre de la campaña", "zh": "活动名称"},
    "label_subject": {"fr": "Objet de l'email", "en": "Email subject", "de": "E-Mail-Betreff", "es": "Asunto del correo", "zh": "邮件主题"},
    "label_sender_name": {"fr": "Nom de l'expéditeur affiché", "en": "Displayed sender name", "de": "Angezeigter Absendername", "es": "Nombre del remitente", "zh": "显示的发件人姓名"},
    "label_sender_email": {"fr": "Email expéditeur", "en": "Sender email", "de": "Absender-E-Mail", "es": "Correo del remitente", "zh": "发件人邮箱"},
    "label_html_template": {"fr": "Modèle HTML de l'email", "en": "Email HTML template", "de": "HTML-Vorlage der E-Mail", "es": "Plantilla HTML del correo", "zh": "邮件 HTML 模板"},
    "label_targets_csv": {
        "fr": "Cibles (une par ligne : email,prenom,nom,departement)",
        "en": "Targets (one per line: email,firstname,lastname,department)",
        "de": "Ziele (eine Zeile pro Person: email,vorname,nachname,abteilung)",
        "es": "Objetivos (uno por línea: email,nombre,apellido,departamento)",
        "zh": "目标名单（每行一个：邮箱,名,姓,部门）",
    },
    "btn_create_campaign": {"fr": "Créer la campagne", "en": "Create campaign", "de": "Kampagne erstellen", "es": "Crear campaña", "zh": "创建活动"},
    "btn_cancel": {"fr": "Annuler", "en": "Cancel", "de": "Abbrechen", "es": "Cancelar", "zh": "取消"},
    "quota_truncated_warning": {
        "fr": "Votre offre ({plan}) limite une campagne à {limit} destinataires : seuls les {limit} premiers de votre liste ont été importés.",
        "en": "Your plan ({plan}) limits a campaign to {limit} recipients: only the first {limit} of your list were imported.",
        "de": "Ihr Tarif ({plan}) begrenzt eine Kampagne auf {limit} Empfänger: nur die ersten {limit} Ihrer Liste wurden importiert.",
        "es": "Tu plan ({plan}) limita una campaña a {limit} destinatarios: solo se importaron los primeros {limit} de tu lista.",
        "zh": "您的套餐（{plan}）每次活动最多 {limit} 个收件人：仅导入了名单中的前 {limit} 个。",
    },

    # ---------------------------------------------------------------- Dashboard
    "back_history": {"fr": "Historique des campagnes", "en": "Campaign history", "de": "Kampagnenverlauf", "es": "Historial de campañas", "zh": "活动历史"},
    "stat_targets": {"fr": "Cibles", "en": "Targets", "de": "Ziele", "es": "Objetivos", "zh": "目标人数"},
    "stat_sent": {"fr": "Envoyés", "en": "Sent", "de": "Gesendet", "es": "Enviados", "zh": "已发送"},
    "stat_rejected": {"fr": "Rejetés", "en": "Rejected", "de": "Abgelehnt", "es": "Rechazados", "zh": "被拒绝"},
    "stat_opened": {"fr": "Ouverts", "en": "Opened", "de": "Geöffnet", "es": "Abiertos", "zh": "已打开"},
    "stat_clicked": {"fr": "Cliqués", "en": "Clicked", "de": "Geklickt", "es": "Clics", "zh": "已点击"},
    "stat_submitted": {"fr": "Ont répondu / soumis", "en": "Submitted / replied", "de": "Formular abgeschickt", "es": "Enviaron el formulario", "zh": "已提交表单"},
    "send_section_title": {"fr": "Envoyer maintenant", "en": "Send now", "de": "Jetzt senden", "es": "Enviar ahora", "zh": "立即发送"},
    "schedule_section_title": {"fr": "Planifier l'envoi", "en": "Schedule the send", "de": "Versand planen", "es": "Programar el envío", "zh": "计划发送"},
    "send_help_intro": {
        "fr": "Ce qu'il faut renseigner, étape par étape :",
        "en": "What to fill in, step by step:",
        "de": "Was Schritt für Schritt auszufüllen ist:",
        "es": "Qué rellenar, paso a paso:",
        "zh": "请按以下步骤填写：",
    },
    "label_provider": {
        "fr": "Fournisseur du compte d'envoi", "en": "Sending account provider",
        "de": "Anbieter des Versandkontos", "es": "Proveedor de la cuenta de envío", "zh": "发件账户提供商",
    },
    "label_smtp_host": {"fr": "Serveur SMTP", "en": "SMTP server", "de": "SMTP-Server", "es": "Servidor SMTP", "zh": "SMTP 服务器"},
    "label_smtp_port": {"fr": "Port", "en": "Port", "de": "Port", "es": "Puerto", "zh": "端口"},
    "label_smtp_user": {"fr": "Utilisateur SMTP (adresse email complète)", "en": "SMTP username (full email address)", "de": "SMTP-Benutzer (vollständige E-Mail-Adresse)", "es": "Usuario SMTP (correo completo)", "zh": "SMTP 用户名（完整邮箱地址）"},
    "label_smtp_pass": {"fr": "Mot de passe / mot de passe d'application", "en": "Password / app password", "de": "Passwort / App-Passwort", "es": "Contraseña / contraseña de aplicación", "zh": "密码/应用专用密码"},
    "label_delay": {"fr": "Délai entre chaque email (ms)", "en": "Delay between each email (ms)", "de": "Verzögerung zwischen E-Mails (ms)", "es": "Retraso entre correos (ms)", "zh": "邮件发送间隔（毫秒）"},
    "label_schedule_dt": {
        "fr": "Date et heure d'envoi", "en": "Send date & time", "de": "Versanddatum und -uhrzeit",
        "es": "Fecha y hora de envío", "zh": "发送日期与时间",
    },
    "btn_send_now": {"fr": "Envoyer aux cibles en attente", "en": "Send to pending targets", "de": "An ausstehende Ziele senden", "es": "Enviar a los pendientes", "zh": "发送给待处理目标"},
    "btn_schedule": {"fr": "Planifier cet envoi", "en": "Schedule this send", "de": "Diesen Versand planen", "es": "Programar este envío", "zh": "计划此次发送"},
    "scheduled_notice": {
        "fr": "Envoi planifié pour le {dt}. Le serveur doit rester allumé et en ligne jusqu'à cette date pour que l'envoi parte automatiquement.",
        "en": "Send scheduled for {dt}. The server must stay running and online until then for the send to fire automatically.",
        "de": "Versand geplant für {dt}. Der Server muss bis dahin laufen und online sein, damit der Versand automatisch erfolgt.",
        "es": "Envío programado para el {dt}. El servidor debe seguir encendido y en línea hasta esa fecha para que el envío se dispare automáticamente.",
        "zh": "已计划于 {dt} 发送。服务器必须在该时间之前持续在线运行，发送才会自动触发。",
    },
    "report_section_title": {"fr": "Rapport pour la direction", "en": "Report for management", "de": "Bericht für die Geschäftsleitung", "es": "Informe para la dirección", "zh": "管理层报告"},
    "report_section_sub": {
        "fr": "Statistiques (avec graphique) + journal nominatif daté, exportable dans le format de votre choix.",
        "en": "Statistics (with chart) + named, dated log, exportable in the format of your choice.",
        "de": "Statistiken (mit Diagramm) + namentliches, datiertes Protokoll, exportierbar im gewünschten Format.",
        "es": "Estadísticas (con gráfico) + registro nominal con fecha, exportable en el formato que prefieras.",
        "zh": "统计数据（含图表）+ 带时间戳的实名记录，可导出为您选择的格式。",
    },
    "log_section_title": {"fr": "Journal par destinataire", "en": "Recipient log", "de": "Protokoll pro Empfänger", "es": "Registro por destinatario", "zh": "收件人记录"},
    "legend_sent": {"fr": "Envoyé", "en": "Sent", "de": "Gesendet", "es": "Enviado", "zh": "已发送"},
    "legend_opened": {"fr": "Ouvert", "en": "Opened", "de": "Geöffnet", "es": "Abierto", "zh": "已打开"},
    "legend_clicked": {"fr": "Cliqué", "en": "Clicked", "de": "Geklickt", "es": "Clic", "zh": "已点击"},
    "legend_submitted": {"fr": "Soumis (le plus critique)", "en": "Submitted (most critical)", "de": "Abgeschickt (am kritischsten)", "es": "Enviado (más crítico)", "zh": "已提交（最严重）"},
    "legend_none": {"fr": "Aucune action", "en": "No action", "de": "Keine Aktion", "es": "Sin acción", "zh": "无操作"},
    "col_email": {"fr": "Email", "en": "Email", "de": "E-Mail", "es": "Correo", "zh": "邮箱"},
    "col_name": {"fr": "Nom", "en": "Name", "de": "Name", "es": "Nombre", "zh": "姓名"},
    "col_department": {"fr": "Service", "en": "Department", "de": "Abteilung", "es": "Departamento", "zh": "部门"},
    "col_status": {"fr": "Statut", "en": "Status", "de": "Status", "es": "Estado", "zh": "状态"},
    "col_last_action": {"fr": "Dernière action", "en": "Last action", "de": "Letzte Aktion", "es": "Última acción", "zh": "最后操作"},

    # ---------------------------------------------------------------- Planifications
    "schedules_title": {"fr": "Planifications", "en": "Scheduled sends", "de": "Planungen", "es": "Programaciones", "zh": "计划任务"},
    "schedules_sub": {
        "fr": "Journal de tous les envois planifiés, toutes entreprises clientes confondues.",
        "en": "Log of all scheduled sends, across every client organisation.",
        "de": "Protokoll aller geplanten Versände, über alle Kundenunternehmen hinweg.",
        "es": "Registro de todos los envíos programados, de todas las empresas clientes.",
        "zh": "所有客户企业计划发送任务的日志。",
    },
    "col_org": {"fr": "Entreprise cliente", "en": "Client organisation", "de": "Kundenunternehmen", "es": "Empresa cliente", "zh": "客户企业"},
    "col_campaign": {"fr": "Campagne", "en": "Campaign", "de": "Kampagne", "es": "Campaña", "zh": "活动"},
    "col_scheduled_for": {"fr": "Planifié pour le", "en": "Scheduled for", "de": "Geplant für", "es": "Programado para", "zh": "计划时间"},
    "sched_status_scheduled": {"fr": "En attente", "en": "Pending", "de": "Ausstehend", "es": "Pendiente", "zh": "待处理"},
    "sched_status_sent": {"fr": "Envoyé", "en": "Sent", "de": "Gesendet", "es": "Enviado", "zh": "已发送"},
    "sched_status_failed": {"fr": "Échoué", "en": "Failed", "de": "Fehlgeschlagen", "es": "Fallido", "zh": "失败"},
    "no_schedules": {
        "fr": "Aucun envoi planifié pour le moment.", "en": "No scheduled sends yet.",
        "de": "Noch keine geplanten Versände.", "es": "Aún no hay envíos programados.", "zh": "暂无计划发送任务。",
    },

    # ---------------------------------------------------------------- Compte
    "account_title": {"fr": "Mon compte", "en": "My account", "de": "Mein Konto", "es": "Mi cuenta", "zh": "我的账户"},
    "label_language": {"fr": "Langue de l'interface", "en": "Interface language", "de": "Oberflächensprache", "es": "Idioma de la interfaz", "zh": "界面语言"},

    # ---------------------------------------------------------------- Awareness (page cible)
    "awareness_title": {
        "fr": "Vous venez de cliquer sur un email de test de phishing",
        "en": "You just clicked a phishing test email",
        "de": "Sie haben gerade auf eine Phishing-Test-E-Mail geklickt",
        "es": "Acabas de hacer clic en un correo de prueba de phishing",
        "zh": "您刚刚点击了一封钓鱼测试邮件",
    },
    "awareness_body": {
        "fr": "Cet email faisait partie d'une simulation interne organisée par votre équipe sécurité. Aucune donnée n'a été compromise : ceci est un exercice de sensibilisation.",
        "en": "This email was part of an internal simulation run by your security team. No data was compromised: this is an awareness exercise.",
        "de": "Diese E-Mail war Teil einer internen Simulation Ihres Sicherheitsteams. Es wurden keine Daten kompromittiert: Dies ist eine Sensibilisierungsübung.",
        "es": "Este correo formaba parte de una simulación interna organizada por tu equipo de seguridad. No se comprometió ningún dato: es un ejercicio de concienciación.",
        "zh": "这封邮件是您的安全团队组织的内部模拟测试。没有任何数据被泄露：这只是一次安全意识演练。",
    },
    "awareness_tips_title": {
        "fr": "Les bons réflexes à retenir", "en": "Good habits to remember",
        "de": "Wichtige Verhaltensregeln", "es": "Buenos hábitos a recordar", "zh": "需要牢记的正确做法",
    },
    "awareness_ack": {"fr": "J'ai compris, merci", "en": "Got it, thanks", "de": "Verstanden, danke", "es": "Entendido, gracias", "zh": "我明白了，谢谢"},
}


def t(key, lang=None):
    lang = lang or DEFAULT_LANG
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get(DEFAULT_LANG) or key
