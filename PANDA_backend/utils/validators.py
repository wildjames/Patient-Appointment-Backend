import ukpostcodeparser
from datetime import datetime, timedelta
import re
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

    # TODO: Do we want something like this, too?
    # if old_status == "missed" and new_status == "active":
    #     # Missed appointments cannot be reactivated, but may be flagged as attended after all, or cancelled
    #     logger.info(f"Cannot reactivate missed appointment")
    #     return False

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


def parse_duration(duration_str):
    """Parse the duration string to get total minutes.

    Returns a timedelta object."""
    hours = 0
    minutes = 0

    # Extract hours and minutes using regex
    matches = re.findall(r"(\d+h)?(\d+m)?", duration_str)
    for match in matches:
        if match[0]:
            hours += int(match[0][:-1])
        if match[1]:
            minutes += int(match[1][:-1])

    return timedelta(hours=hours, minutes=minutes)


def check_if_missed_appointment(appointment):
    """Check if the appointment was missed. Returns a boolean."""
    # If we have a model, convert it to a dictionary
    if hasattr(appointment, "serialize"):
        appointment = appointment.serialize()
    
    # Only active appointments can be missed
    if appointment["status"] != "active":
        logger.info(
            f"[{appointment['id']}] Appointment is not active, so cannot be missed"
        )
        return False

    # Parse the start time of the appointment
    start_time_str = appointment["time"]
    start_time = datetime.fromisoformat(start_time_str)

    # Parse the duration of the appointment
    duration_str = appointment["duration"]
    duration = parse_duration(duration_str)

    # Calculate the end time of the appointment
    end_time = start_time + duration
    logger.debug(f"[{appointment['id']}] Appointment end time: {end_time}")

    # Get the current time
    current_time = datetime.now().astimezone(start_time.tzinfo)
    logger.debug(f"[{appointment['id']}] Current time: {current_time}")

    is_missed = current_time > end_time
    logger.debug(
        f"[{appointment['id']}] Checking if appointment was missed: {is_missed}"
    )

    # Check if the current time is greater than the end time of the appointment
    return is_missed
