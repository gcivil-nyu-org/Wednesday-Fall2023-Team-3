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
LARGE_CAPACITY = 50

TAG_ICON_PATHS = [
    "static/events/images/boombox.svg",
    "static/events/images/cup-hot.svg",
    "static/events/images/person-arms-up.svg",
    "static/events/images/moon.svg",
    "static/events/images/easel.svg",
    "static/events/images/book.svg",
]
