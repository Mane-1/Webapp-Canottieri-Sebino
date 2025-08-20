# Package models per Canottieri Sebino
# Contiene tutti i modelli del sistema

# Import dei modelli base
from .base_models import *

# Import dei modelli per le attività
from .activities import (
    ActivityType, QualificationType, Activity, UserQualification,
    ActivityRequirement, ActivityAssignment, ActivityAudit
)
