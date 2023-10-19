import ukpostcodeparser
from logging import getLogger

logger = getLogger(__name__)


def is_valid_appointment_status(status):
    return status in ["active", "cancelled", "missed", "attended"]


def is_valid_state_change(old_status, new_status):
    """Appointments can be cancelled, but cancelled appointments cannot be reinstated."""
    if old_status == "active" and new_status in [
        "attended",
        "cancelled",
        "missed",
        "active",
    ]:
        # Active appointments can be updated to anything
        return True

    if old_status == "cancelled" and new_status == "active":
        # Cancelled appointments cannot be reactivated
        logger.info(f"Cannot reactivate cancelled appointment")
        return False

    if old_status == "missed" and new_status == "active":
        # Missed appointments cannot be reactivated, but may be flagged as attended after all, or cancelled
        logger.info(f"Cannot reactivate missed appointment")
        return False

    return True


def validate_nhs_number(nhs_number):
    # TODO: Implement this: https://www.datadictionary.nhs.uk/attributes/nhs_number.html
    # Return True if valid, False otherwise
    return True


def format_postcode(postcode):
    """Leverage the ukpostcodeparser library to coerce a postcode into the correct format.
    
    Returns the postcode in the format "AA11 1AA" or None if the postcode is invalid.
    """
    logger.info(f"Formatting postcode: {postcode}")
    try:
        postcode_chunks = ukpostcodeparser.parse_uk_postcode(postcode, False, True)
        logger.info(f"Parsed postcode {postcode} into chunks: {postcode_chunks}")
    except:
        return None

    return " ".join(postcode_chunks)
