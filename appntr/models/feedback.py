from django.db import models
from django.conf import settings
from .general import Application


class Feedback(models.Model):
    class TYPES:
        YES = "yes"
        NO = "no"
        MAYBE = "maybe"
        MISSED = "missed"
        RECALL_YES = "recall_yes"
        RECALL_NO = "recall_no"
        RECALL_MAYBE = "recall_maybe"

    class STATUS:
        OPEN = "open"
        DONE = "done"

    added_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="feedbacks")
    application = models.ForeignKey(Application, related_name="feedbacks")
    status = models.CharField(null=False, blank=False, default=STATUS.OPEN, max_length=255, verbose_name="Status", choices = [
        (STATUS.OPEN, "offen"),
        (STATUS.DONE, "erledigt")
    ])
    done_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    done_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    interviewer_names = models.CharField(null=False, blank=False, max_length=255, verbose_name="Namen der beiden DiB-Gesprächspartner*innen")

    feedback_type = models.CharField(db_index=True, max_length=25, verbose_name="Rückmeldung", choices= [
        (TYPES.YES, "Ja, aufnehmen"),
        (TYPES.NO, "Nein, nicht aufnehmen"),
        (TYPES.MAYBE, "Wir können uns nicht einigen. Bitte erneut einladen."),
        (TYPES.MISSED, "Person ist nicht zum Termin erschienen"),
        (TYPES.RECALL_YES, "Gespräch einzeln geführt, meine Empfehlung: ja, aufnehmen --> bitte zweiten Gesprächspartner organisieren"),
        (TYPES.RECALL_NO, "Gespräch einzeln geführt, meine Empfehlung: nein, nicht aufnehmen --> bitte zweiten Gesprächspartner organisieren"),
        (TYPES.RECALL_MAYBE, "Gespräch einzeln geführt, meine Empfehlung:bin mir unsicher --> bitte zwei neue Gesprächspartner organisieren")
    ])

    statement_yes = models.TextField(null=True, blank=True, verbose_name="BEI ZUSAGE: Kompetenzen für Mitarbeit", help_text="Bitte diesen Teil nur bei Zusage ausfüllen")
    statement_maybe = models.TextField(null=True, blank=True, verbose_name="BEI UNSICHERHEIT/ UNEINIGKEIT: Kurze Begründung", help_text="Bitte gebt den nächsten Gesprächspartnern mit auf den Weg, wo ihr unsicher seid")
    statement_no = models.TextField(null=True, blank=True, verbose_name="BEI ABSAGE: kurze, sachliche Begründung", help_text="Bitte diesen Teil nur bei Absage ausfüllen, bitte sachlich schreiben (bspw. passt nicht zu den Werten etc.)")

    class Meta:
        app_label = 'appntr'