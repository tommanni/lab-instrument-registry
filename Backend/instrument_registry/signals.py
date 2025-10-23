def add_history_username(sender, **kwargs):
    history_instance = kwargs['history_instance']
    if history_instance.history_user:
        history_instance.history_username = history_instance.history_user.full_name
