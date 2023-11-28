# constans are defined here

PENDING = "pending"
WITHDRAWN = "withdrawn"
APPROVED = "approved"
REJECTED = "rejected"
REMOVED = "removed"

STATUS_CHOICES = (
    (PENDING, "Pending"),
    (WITHDRAWN, "Withdrawn"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected"),
    (REMOVED, "Removed"),
)

CHEER_UP = "🎉"
THUMBS_UP = "👍"
HEART = "❤️"
CLAP = "👏"
HIGH_FIVE = "🙌"

EMOJI_CHOICES = (
    (CHEER_UP, "Cheer up"),
    (THUMBS_UP, "Thumbs up"),
    (HEART, "Heart"),
    (CLAP, "Clap"),
    (HIGH_FIVE, "High five"),
)

SMALL_CAPACITY = 5
MEDIUM_CAPACITY = 20
LARGE_CAPCAITY = 50
