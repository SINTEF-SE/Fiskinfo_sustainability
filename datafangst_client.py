
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import requests
import pandas as pd
from PySide6.QtCore import QDate

from utility import getMonthTimestamps


# ------------------------------------------------------------
# Logging configuration
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ------------------------------------------------------------
# Clean Datafangst API Client
# ------------------------------------------------------------
class DatafangstClient:
    def __init__(self, token: Optional[str] = None, base_url: str = None):
        """
        Initialize the API client.

        token     : OAuth2 Bearer token (recommended: set via env var)
        base_url  : Base API endpoint
        """

        self.base_url = base_url or "https://api.dev.datafangst.orcalabs.no/"

        #self.token = token or os.environ.get("DATAFANGST_TOKEN")
        self.token = "dcyerkjerfklfvn"                                  # TESTING ONLY!!!
        if not self.token:
            raise ValueError("Missing API token. Set DATAFANGST_TOKEN environment variable.")

        # A persistent session is faster
        self.session = requests.Session()
        self.session.hooks["response"].append(self._log_response)

    # ------------------------------------------------------------
    # Internal logging
    # ------------------------------------------------------------
    def _log_response(self, response, *args, **kwargs):
        logging.info(f"API Request: {response.url}")
        logging.info(f"Status: {response.status_code}, Bytes: {len(response.content)}")

    # ------------------------------------------------------------
    # Header builder
    # ------------------------------------------------------------
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    # ------------------------------------------------------------
    # CSV Writer
    # ------------------------------------------------------------
    def json_to_csv(self, json_data: Any, output_file: str, append: bool = False):
        try:
            # Ensure folder exists
            folder = os.path.dirname(output_file)
            if folder:
                os.makedirs(folder, exist_ok=True)

            df = pd.json_normalize(json_data)
            df.to_csv(
                output_file,
                index=False,
                encoding="utf-8-sig",
                mode="a" if append else "w",
                header=not append
            )

            logging.info(f"CSV saved: {output_file}")
        except Exception as e:
            logging.error(f"CSV write error: {e}")

    # ------------------------------------------------------------
    # Build API query parameters
    # ------------------------------------------------------------
    def build_params(
        self,
        request_type: str,
        sDate: Optional[QDate],
        eDate: Optional[QDate],
        vesselGroups: List[str],
        gearGroups: List[str],
        speciesGroups: List[str],
        locationGroups: List[str],
        limit: int,
        offset: int,
        vesselId: Optional[int],
    ) -> Dict[str, Any]:

        params: Dict[str, Any] = {}

        # Expand QDate → ISO time
        if request_type.endswith("/hauls"):
            # Uses month timestamps
            params["months[]"] = getMonthTimestamps(sDate, eDate)

        else:
            if sDate and sDate.isValid():
                params["start"] = f"{sDate.toPython()}T00:00:00.000Z"

            if eDate and eDate.isValid():
                params["end"] = f"{eDate.toPython()}T23:59:59.999Z"

        # ------------------------------------------------------------------
        # Filters
        # ------------------------------------------------------------------
        if vesselGroups:
            params["vesselLengthGroups"] = vesselGroups

        if gearGroups:
            params["gearGroupIds"] = gearGroups

        if speciesGroups:
            params["speciesGroupIds"] = speciesGroups

        if locationGroups:
            params["catchLocations[]"] = locationGroups

        if vesselId:
            params["vesselIds"] = [vesselId]   # API expects list

        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        return params

    # ------------------------------------------------------------
    # Perform API request
    # ------------------------------------------------------------
    
    def request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        csv_file: str = "",
        append_csv: bool = False,
        log_json: bool = False,
        print_out = False,
        auth: bool = False
    ):
            
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            url = self.base_url + endpoint


        # Build headers conditionally
        headers = {"accept": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            resp = self.session.get(url, headers=headers, params=params)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

        try:
            data = resp.json()
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON:\n{resp.text}")
            return None

        if csv_file:
            self.json_to_csv(data, csv_file, append_csv)

        if log_json:
            logging.info(json.dumps(data, indent=2))

        
        if print_out:
            print("\n========== API RESULT ==========")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("================================\n")


        return data


        # ------------------------------------------------------------
        # High-level API request helper
        # ------------------------------------------------------------
        
    def get(
        self,
        request_type: str,
        sDate=QDate(),
        eDate=QDate(),
        vesselGroups=None,
        gearGroups=None,
        speciesGroups=None,
        locationGroups=None,
        limit: int = 0,
        offset: int = 0,
        vesselId: Optional[int] = None,
        csv_file: str = "",
        append_csv: bool = False,
        log_json: bool = False,
        print_out: bool = False,
        auth: bool = False
    ):
        params = self.build_params(
            request_type=request_type,
            sDate=sDate,
            eDate=eDate,
            vesselGroups=vesselGroups or [],
            gearGroups=gearGroups or [],
            speciesGroups=speciesGroups or [],
            locationGroups=locationGroups or [],
            limit=limit,
            offset=offset,
            vesselId=vesselId,
        )

        return self.request(
            endpoint=request_type,
            params=params,
            csv_file=csv_file,
            append_csv=append_csv,
            log_json=log_json,
            print_out=print_out,
            auth=auth
        )

