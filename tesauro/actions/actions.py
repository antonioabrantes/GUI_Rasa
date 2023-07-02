# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

import arrow
import dateparser

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from typing import Any, Text, Dict, List ## Datatypes
import re

ALLOWED_PIZZA_SIZES = ("s", "m", "l", "xl")
ALLOWED_PIZZA_TYPES = ("fungi", "hawai", "pepperoni", "mozarella", "veggie")
VEGETARIAN_PIZZAS = ("fungi", "mozarella", "veggie")
VEGETARIAN_PIZZAS = ("hawai", "pepperoni")


class ValidateSimplePizzaForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_simple_pizza_form"

    def validate_pizza_size(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate 'pizza_size' value. """

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f"We only accept pizza sizes: s/m/l/xl.")
            return {"pizza_size": None}

        dispatcher.utter_message(text=f"Ok! You want to have a {slot_value} pizza.")
        return {"pizza_size": slot_value}

    def validate_pizza_type(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate 'pizza_type' value. """

        if slot_value.lower() not in ALLOWED_PIZZA_TYPES:
            dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}.")
            return {"pizza_type": None}

        dispatcher.utter_message(text=f"Ok! You want to have a {slot_value} pizza.")
        return {"pizza_type": slot_value}


city_db = {
    'brussles': 'Europe/Brussels',
    'zagreb': 'Europe/Zagreb',
    'london': 'Europe/London',
    'lisbon': 'Europe/Lisbon',
    'amsterdam': 'Europe/Amsterdam',
    'seattle': 'US/Pacific'
}


class ActionTellTime(Action):

    def name(self) -> Text:
        return "action_tell_time"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        current_place = next(tracker.get_latest_entity_values("place"), None)
        utc = arrow.utcnow()

        if not current_place:
            msg = f"It's {utc.format('HH:mm')} utc now. You can also give me a place."
            dispatcher.utter_message(text=msg)
            return []

        current_place_lower = current_place.lower()
        tz_string = city_db.get(current_place_lower, None)
        if not tz_string:
            msg = f"It's I didn't recognize {current_place}. Is it spelled correctly?"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"It's {utc.to(city_db[current_place_lower]).format('HH:mm')} in {current_place} now"
        dispatcher.utter_message(text=msg)
        return []


class ActionRememberWhere(Action):

    def name(self) -> Text:
        return "action_remember_where"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        current_place = next(tracker.get_latest_entity_values("place"), None)
        utc = arrow.utcnow()

        if not current_place:
            msg = f"I didn't get where you lived. Are you sure it's spelled correctly ?"
            dispatcher.utter_message(text=msg)
            return []

        current_place_lower = current_place.lower()
        tz_string = city_db.get(current_place_lower, None)
        if not tz_string:
            msg = f"It's I didn't recognize {current_place}. Is it spelled correctly?"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"Sure thing! I'll remember that you live in {current_place}"
        dispatcher.utter_message(text=msg)
        return [SlotSet("location", current_place)]


class ActionAnswerWhere(Action):

    def name(self) -> Text:
        return "action_answer_where"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        current_place = tracker.get_slot("location")

        if not current_place:
            msg = f"I don't know where you live"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"You live in {current_place}"
        dispatcher.utter_message(text=msg)
        return []


class ActionTimeDifference(Action):

    def name(self) -> Text:
        return "action_time_difference"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        timezone_to = next(tracker.get_latest_entity_values("place"), None)
        timezone_in = tracker.get_slot("location")

        timezone_to = timezone_to.lower()
        timezone_in = timezone_in.lower()

        #dispatcher.utter_message(text=timezone_in)
        #return []

        if not timezone_in:
            msg = f"To calculate the time difference I need to know where you live"
            dispatcher.utter_message(text=msg)
            return []

        if not timezone_to:
            msg = f"I didn't the timezone you'd like to compare against. are you sure it's spelled correctly ?"
            dispatcher.utter_message(text=msg)
            return []

        tz_string = city_db.get(timezone_to, None)
        if not tz_string:
            msg = f"I didn't recognize {timezone_to}. Is it spelled correctly?"
            dispatcher.utter_message(text=msg)
            return []

        t1 = arrow.utcnow().to(city_db[timezone_to])
        t2 = arrow.utcnow().to(city_db[timezone_in])
        max_t, min_t = max(t1, t2), min(t1, t2)
        diff_seconds = dateparser.parse(str(max_t)[:19]) - dateparser.parse(str(min_t)[:19])
        diff_hours = int(diff_seconds.seconds / 3600)
        interval_seconds = abs(max_t.timestamp() - min_t.timestamp())
        interval_hours = int(interval_seconds / 3600)
        # msg = f"There is a {min(diff_hours, 24 - diff_hours)}H time difference."
        msg = f"There is a {interval_hours}H time difference {interval_seconds} - {max_t} {min_t}."
        dispatcher.utter_message(text=msg)
        return []


class ActionClearPizza(Action):

    def name(self) -> Text:
        return "action_clear_pizza"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Pizza cleared! You can ask a new pizza")
        return [SlotSet("pizza_type", None), SlotSet("pizza_size", None)]


class AskForPizzaTypeAction(Action):

    def name(self) -> Text:
        return "action_ask_pizza_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict) -> List[Dict[Text, Any]]:

        if tracker.get_slot("vegetarian"):
            dispatcher.utter_message(text=f"What kind of pizza you want?", buttons=[{"title":p,"payload":p} for p in VEGETARIAN_PIZZAS])
        elif tracker.get_slot("vegetarian") == False:
            dispatcher.utter_message(text=f"What kind of pizza you want?", buttons=[{"title":p,"payload":p} for p in MEAT_PIZZAS])
        else:
            dispatcher.utter_message(text=f"What kind of pizza you would like to buy?")

        return []


class AskForVegeterianAction(Action):

    def name(self) -> Text:
        return "action_ask_vegetarian"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Would you like to order a vegetarian pizza ?", buttons=[{"title":"yes","payload":"/affirm"},{"title":"no","payload":"/deny"}])
        return []


class ValidateFancyPizzaForm(Action):

    def name(self) -> Text:
         return "validate_fancy_pizza_form"

    def validate_vegetarian(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate pizza size."""
        if tracker.get_intent_of_latest_message() == "affirm":
            dispatcher.utter_message("I'll remember you prefer vegetarian")
            return {"vegetarian": True}
        if tracker.get_intent_of_latest_message() == "deny":
            dispatcher.utter_message("I'll remember you don't want vegetarian pizza")
            return {"vegetarian": False}
        dispatcher.utter_message("I didn't get that.")
        return {"vegetarian": None}

    def validate_pizza_size(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate 'pizza_size' value. """

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f"We only accept pizza sizes: s/m/l/xl.")
            return {"pizza_size": None}

        dispatcher.utter_message(text=f"Ok! You want to have a {slot_value} pizza.")
        return {"pizza_size": slot_value}

    def validate_pizza_type(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate 'pizza_type' value. """

        if slot_value.lower() not in ALLOWED_PIZZA_TYPES:
            dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}.")
            return {"pizza_type": None}

        dispatcher.utter_message(text=f"Ok! You want to have a {slot_value} pizza.")
        return {"pizza_type": slot_value}

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")
        return []


class ActionSearch(Action):

    def name(self) -> Text:
        return "action_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Calling the DB
        # calling an API
        # do anything
        # all caluculations are done
        camera = tracker.get_slot('camera')
        ram = tracker.get_slot('RAM')
        battery = tracker.get_slot('battery')

        dispatcher.utter_message(text='Here are your search results')
        dispatcher.utter_message(
            text='The features you entered: ' + str(camera) + ", " + str(ram) + ", " + str(battery))
        return []


########################

class ActionShowLatestNews(Action):

    def name(self) -> Text:
        return "action_show_latest_news"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Calling the DB
        # calling an API
        # do anything
        # all caluculations are done
        dispatcher.utter_message(text='Here the latest news for your category')

        return []


class ProductSearchForm(FormValidationAction):
    """Example of a custom form action"""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "product_search_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return ["ram", "battery", "camera", "budget"]

        # def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        # return []

    def validate_ram(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate num_people value."""
        # 4 GB RAM
        # 10 GB RAM --> integers/number from this -- 10
        #
        ram_int = int(re.findall(r'[0-9]+', value)[0])
        # Query the DB and check the max value, that way it can be dynamic
        if ram_int < 50:
            return {"ram": ram_int}
        else:
            dispatcher.utter_message(template="utter_wrong_ram")

            return {"ram": None}

    def validate_camera(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate num_people value."""
        # 4 GB RAM
        # 10 GB RAM --> integers/number from this -- 10
        #
        camera_int = int(re.findall(r'[0-9]+', value)[0])
        # Query the DB and check the max value, that way it can be dynamic
        if camera_int < 150:
            return {"camera": camera_int}
        else:
            dispatcher.utter_message(template="utter_wrong_camera")

            return {"camera": None}

    def validate_budget(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate num_people value."""
        # 4 GB RAM
        # 10 GB RAM --> integers/number from this -- 10
        #
        budget_int = int(re.findall(r'[0-9]+', value)[0])
        # Query the DB and check the max value, that way it can be dynamic
        if budget_int < 4000:
            return {"budget": budget_int}
        else:
            dispatcher.utter_message(template="utter_wrong_budget")

            return {"budget": None}

    def validate_battery(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate num_people value."""
        # 4 GB RAM
        # 10 GB RAM --> integers/number from this -- 10
        #
        battery_int = int(re.findall(r'[0-9]+', value)[0])
        # Query the DB and check the max value, that way it can be dynamic
        if battery_int < 50:
            return {"battery": battery_int}
        else:
            dispatcher.utter_message(template="utter_wrong_battery")

            return {"battery": None}

    # USED FOR DOCS: do not rename without updating in docs
    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        dispatcher.utter_message(text="Please find your searched items here.........")

        return []