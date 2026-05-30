"""Build bilingual PDF report: Overview + Sentiment Analysis."""

import io
from datetime import datetime
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_DIR = Path(__file__).resolve().parent / 'fonts'
FONT_REG = 'Amiri'
FONT_BOLD = 'Amiri-Bold'

_LABELS = {
    'ar': {
        'title': 'تقرير Analytica',
        'generated': 'تاريخ الإنشاء',
        'period': 'الفترة',
        'all_period': 'كل البيانات المتاحة',
        'overview': '١. نظرة عامة',
        'sentiment': '٢. تحليل المشاعر',
        'metric': 'المؤشر',
        'value': 'القيمة',
        'total_posts': 'إجمالي المنشورات',
        'total_comments': 'إجمالي التعليقات',
        'linked_accounts': 'الحسابات المربوطة',
        'completed_scrapes': 'عمليات المزامنة الناجحة',
        'total_likes': 'إجمالي الإعجابات',
        'total_shares': 'إجمالي المشاركات',
        'total_interactions': 'إجمالي التفاعلات',
        'pos_pct': 'نسبة الإيجابي',
        'neg_pct': 'نسبة السلبي',
        'neu_pct': 'نسبة المحايد',
        'pos_count': 'تعليقات إيجابية',
        'neg_count': 'تعليقات سلبية',
        'neu_count': 'تعليقات محايدة',
        'csat': 'مؤشر رضا العملاء (CSAT)',
        'top_topics': 'أبرز المواضيع',
        'topic': 'الموضوع',
        'count': 'العدد',
        'dominant_sentiment': 'المشاعر السائدة',
        'volume_timeline': 'حجم البيانات اليومي',
        'date': 'التاريخ',
        'posts': 'منشورات',
        'comments': 'تعليقات',
        'engagement_timeline': 'التفاعل على المنشورات',
        'likes': 'إعجابات',
        'shares': 'مشاركات',
        'interactions': 'تفاعلات',
        'sentiment_timeline': 'تطور مشاعر التعليقات',
        'positive': 'إيجابي',
        'negative': 'سلبي',
        'neutral': 'محايد',
        'no_data': 'لا توجد بيانات في هذه الفترة',
    },
    'en': {
        'title': 'Analytica Report',
        'generated': 'Generated',
        'period': 'Period',
        'all_period': 'All available data',
        'overview': '1. Overview',
        'sentiment': '2. Sentiment Analysis',
        'metric': 'Metric',
        'value': 'Value',
        'total_posts': 'Total posts',
        'total_comments': 'Total comments',
        'linked_accounts': 'Linked accounts',
        'completed_scrapes': 'Successful syncs',
        'total_likes': 'Total likes',
        'total_shares': 'Total shares',
        'total_interactions': 'Total interactions',
        'pos_pct': 'Positive %',
        'neg_pct': 'Negative %',
        'neu_pct': 'Neutral %',
        'pos_count': 'Positive comments',
        'neg_count': 'Negative comments',
        'neu_count': 'Neutral comments',
        'csat': 'Customer satisfaction (CSAT)',
        'top_topics': 'Top topics',
        'topic': 'Topic',
        'count': 'Count',
        'dominant_sentiment': 'Dominant sentiment',
        'volume_timeline': 'Daily data volume',
        'date': 'Date',
        'posts': 'Posts',
        'comments': 'Comments',
        'engagement_timeline': 'Post engagement',
        'likes': 'Likes',
        'shares': 'Shares',
        'interactions': 'Interactions',
        'sentiment_timeline': 'Comment sentiment over time',
        'positive': 'Positive',
        'negative': 'Negative',
        'neutral': 'Neutral',
        'no_data': 'No data for this period',
    },
}


def _register_fonts():
    reg_path = FONT_DIR / 'Amiri-Regular.ttf'
    bold_path = FONT_DIR / 'Amiri-Bold.ttf'
    if reg_path.exists() and FONT_REG not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REG, str(reg_path)))
    if bold_path.exists() and FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold_path)))


def _shape(text, lang):
    if text is None:
        return ''
    s = str(text)
    if lang != 'ar':
        return s
    if not any('\u0600' <= c <= '\u06FF' for c in s):
        return s
    return get_display(arabic_reshaper.reshape(s))


def _t(key, lang):
    return _LABELS.get(lang, _LABELS['en']).get(key, key)


def _p(text, style):
    return Paragraph(text.replace('\n', '<br/>'), style)


def _styles(lang):
    align = TA_RIGHT if lang == 'ar' else TA_LEFT
    return {
        'title': ParagraphStyle('title', fontName=FONT_BOLD, fontSize=20, alignment=TA_CENTER, leading=26),
        'h2': ParagraphStyle('h2', fontName=FONT_BOLD, fontSize=14, alignment=align, leading=20, spaceAfter=8),
        'body': ParagraphStyle('body', fontName=FONT_REG, fontSize=10, alignment=align, leading=14),
        'cell': ParagraphStyle('cell', fontName=FONT_REG, fontSize=9, alignment=align, leading=12),
        'cell_hdr': ParagraphStyle('cell_hdr', fontName=FONT_BOLD, fontSize=9, alignment=align, leading=12),
    }


def _table(rows, col_widths=None):
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), FONT_REG),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def _kpi_table(snapshot, lang, styles):
    s = snapshot
    eng = s['engagement_summary']
    rows = [
        [_p(_shape(_t('metric', lang), lang), styles['cell_hdr']), _p(_shape(_t('value', lang), lang), styles['cell_hdr'])],
        [_p(_shape(_t('total_posts', lang), lang), styles['cell']), _p(str(s['total_posts']), styles['cell'])],
        [_p(_shape(_t('total_comments', lang), lang), styles['cell']), _p(str(s['total_comments']), styles['cell'])],
        [_p(_shape(_t('linked_accounts', lang), lang), styles['cell']), _p(str(s['linked_accounts']), styles['cell'])],
        [_p(_shape(_t('completed_scrapes', lang), lang), styles['cell']), _p(str(s['completed_scrapes']), styles['cell'])],
        [_p(_shape(_t('total_likes', lang), lang), styles['cell']), _p(str(eng['likes']), styles['cell'])],
        [_p(_shape(_t('total_shares', lang), lang), styles['cell']), _p(str(eng['shares']), styles['cell'])],
        [_p(_shape(_t('total_interactions', lang), lang), styles['cell']), _p(str(eng['interactions']), styles['cell'])],
    ]
    return _table(rows, [10 * cm, 7 * cm])


def _sentiment_kpi_table(snapshot, lang, styles):
    sent = snapshot['sentiment_summary']
    rows = [
        [_p(_shape(_t('metric', lang), lang), styles['cell_hdr']), _p(_shape(_t('value', lang), lang), styles['cell_hdr'])],
        [_p(_shape(_t('pos_pct', lang), lang), styles['cell']), _p(f"{sent['pos_pct']}% ({sent['pos_count']})", styles['cell'])],
        [_p(_shape(_t('neg_pct', lang), lang), styles['cell']), _p(f"{sent['neg_pct']}% ({sent['neg_count']})", styles['cell'])],
        [_p(_shape(_t('neu_pct', lang), lang), styles['cell']), _p(f"{sent['neu_pct']}% ({sent['neu_count']})", styles['cell'])],
        [_p(_shape(_t('csat', lang), lang), styles['cell']), _p(str(sent['csat']), styles['cell'])],
    ]
    return _table(rows, [10 * cm, 7 * cm])


def _topics_table(snapshot, lang, styles):
    topics = snapshot['top_topics']
    if not topics:
        return _p(_shape(_t('no_data', lang), lang), styles['body'])
    rows = [[
        _p(_shape(_t('topic', lang), lang), styles['cell_hdr']),
        _p(_shape(_t('count', lang), lang), styles['cell_hdr']),
        _p(_shape(_t('dominant_sentiment', lang), lang), styles['cell_hdr']),
    ]]
    for item in topics:
        rows.append([
            _p(_shape(item['topic'], lang), styles['cell']),
            _p(str(item['count']), styles['cell']),
            _p(_shape(item['sentiment'], lang), styles['cell']),
        ])
    return _table(rows, [8 * cm, 3 * cm, 6 * cm])


def _timeline_table(rows_data, headers, lang, styles, col_widths):
    if not rows_data:
        return _p(_shape(_t('no_data', lang), lang), styles['body'])
    rows = [[_p(_shape(h, lang), styles['cell_hdr']) for h in headers]]
    for row in rows_data[:20]:
        rows.append([_p(_shape(str(v), lang), styles['cell']) for v in row])
    return _table(rows, col_widths)


def build_report_pdf(snapshot, lang='ar', report_title=None):
    _register_fonts()
    lang = 'ar' if lang == 'ar' else 'en'
    styles = _styles(lang)
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=report_title or _t('title', lang),
    )

    period = _t('all_period', lang)
    if snapshot.get('period_from') or snapshot.get('period_to'):
        period = f"{snapshot.get('period_from') or '…'} → {snapshot.get('period_to') or '…'}"

    story = [
        _p(_shape(report_title or _t('title', lang), lang), styles['title']),
        Spacer(1, 0.4 * cm),
        _p(_shape(f"{_t('generated', lang)}: {datetime.now().strftime('%Y-%m-%d %H:%M')}", lang), styles['body']),
        _p(_shape(f"{_t('period', lang)}: {period}", lang), styles['body']),
        Spacer(1, 0.6 * cm),
        _p(_shape(_t('overview', lang), lang), styles['h2']),
        _kpi_table(snapshot, lang, styles),
        Spacer(1, 0.4 * cm),
        _p(_shape(_t('top_topics', lang), lang), styles['h2']),
        _topics_table(snapshot, lang, styles),
        Spacer(1, 0.4 * cm),
        _p(_shape(_t('volume_timeline', lang), lang), styles['h2']),
        _timeline_table(
            [[r['date'], r['posts'], r['comments']] for r in snapshot['timeline']],
            [_t('date', lang), _t('posts', lang), _t('comments', lang)],
            lang, styles, [5 * cm, 4 * cm, 4 * cm],
        ),
        Spacer(1, 0.4 * cm),
        _p(_shape(_t('engagement_timeline', lang), lang), styles['h2']),
        _timeline_table(
            [[r['date'], r['likes'], r['shares'], r['interactions']] for r in snapshot['engagement_timeline']],
            [_t('date', lang), _t('likes', lang), _t('shares', lang), _t('interactions', lang)],
            lang, styles, [4 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm],
        ),
        PageBreak(),
        _p(_shape(_t('sentiment', lang), lang), styles['h2']),
        _sentiment_kpi_table(snapshot, lang, styles),
        Spacer(1, 0.4 * cm),
        _p(_shape(_t('sentiment_timeline', lang), lang), styles['h2']),
        _timeline_table(
            [[r['date'], r['pos'], r['neg'], r['neu']] for r in snapshot['timeline']],
            [_t('date', lang), _t('positive', lang), _t('negative', lang), _t('neutral', lang)],
            lang, styles, [4 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm],
        ),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
