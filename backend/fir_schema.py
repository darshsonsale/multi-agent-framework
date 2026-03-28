FIR_SCHEMA = {
    "complainant": {
        "personal_info": {
            "nature_of_complaint": {"required": True}
        },
    },

    "accused": {
        "name_of_accused": {"required": False},
        "address_of_accused": {"required": False},
    },

    "incident": {
        "place_of_incident": {"required": True},
        "type_of_incident": {"required": False},
        "date_of_incident": {"required": True},
        "time_of_incident": {"required": True},
    },

    "complaint_submission": {
        "knows_police_station": {"required": True},
        "police_station": {"required": True}
    },

    "complaint_detail": {
        "complaint_description": {"required": True},
        "date_of_complaint": {"required": False},
        "remarks": {"required": False},
    }
}