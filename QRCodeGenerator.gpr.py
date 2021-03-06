register(REPORT,
    id   = 'QRCodeGenerator',
    name = _('QRCodeGenerator'),
    description = _("Produces a report of QRCodes about individuals "),
    version = '1.0',
    gramps_target_version = '4.1',
    status = STABLE,
    fname = 'QRCodeGenerator.py',
    authors = ["Derik Pack"],
    authors_email = ["bob@email.com"],
    category = CATEGORY_TEXT,
    reportclass = 'QRCodeGenerator',
    optionclass = 'QRCodeOptions',
    report_modes = [REPORT_MODE_GUI],
    require_active = True
    )
