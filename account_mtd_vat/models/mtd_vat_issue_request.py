# -*- coding: utf-8 -*-

import requests
import json
import logging
import werkzeug

from openerp import models, fields, api, exceptions
from datetime import datetime

_logger = logging.getLogger(__name__)


class MtdVatIssueRequest(models.Model):
    _name = 'mtd_vat.issue_request'
    _description = "VAT issues connection request step - 3"

    @api.multi
    def json_command(self, command, module_name=None, record_id=None, api_tracker=None, timeout=3):
        try:
            record = self.env[module_name].search([('id', '=', record_id)])
            _logger.info(
                "json_command - we need to find the record and assign it to self"
            )
            token_record = self.env['mtd.api_tokens'].search([('api_id', '=', record.api_id.id)])
            access_token = token_record.access_token if token_record else ""
            # may not newed next line of code will need to look into this further while testing.
            # refresh_token = token_record.refresh_token if token_record else ""

            header_items = {"Accept": "application/vnd.hmrc.1.0+json"}
            if record.endpoint_name in ("vat-obligation", "vat-liabilities", "vat-payments"):
                header_items["authorization"] = ("Bearer " + str(access_token))
                header_items["Content-Type"] = ("application/json")

            hmrc_connection_url = "{}{}?from={}&to={}".format(
                record.hmrc_configuration.hmrc_url, record.path, record.date_from, record.date_to)

            _logger.info(
                "json_command - hmrc connection url:- {connection_url}, ".format(connection_url=hmrc_connection_url) +
                "headers:- {header}".format(header=header_items)
            )
            response = requests.get(hmrc_connection_url, timeout=timeout, headers=header_items)
            import pdb; pdb.set_trace()
            return self.handle_request_response(response, record, hmrc_connection_url, token_record, api_tracker)
        except ValueError:
            api_tracker.closed = 'error'

            if api_tracker:
                return werkzeug.utils.redirect(
                    "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=module_name) +
                    "menu_id={menu}&action={action}".format(menu=api_tracker.menu_id, action=api_tracker.action)
                )
            return True

    def handle_request_response(self, response, record=None, url=None, api_token_record=None, api_tracker=None):
        response_token = json.loads(response.text)
        if api_tracker:
            action = api_tracker.action
            menu_id = api_tracker.menu_id
            module_name = api_tracker.module_name
        _logger.info(
            "json_command - received respponse of the request:- {response}, ".format(response=response) +
            "and its text:- {response_token}".format(response_token=response_token)
        )
        import pdb;pdb.set_trace()
        if response.ok:
            if record.endpoint_name == "vat-obligation":
                self.add_obligation_logs(response)
            elif record.endpoint_name == "vat-liabilities":
                self.add_liabilities_logs(response)
            elif record.endpoint_name == "vat-payments":
                self.add_payments_logs(response, record)
            return self.process_successful_response(record, api_tracker)

        elif (response.status_code == 401 and
              response_token['message'] == "Invalid Authentication information provided"):
            _logger.info(
                "json_command - code 401 found, user button clicked,  " +
                "and message was:- {} ".format(response_token['message'])
            )

            import pdb;pdb.set_trace()
            return self.env['mtd.refresh_authorisation'].refresh_user_authorisation(record, api_token_record)

        else:
            response_token = json.loads(response.text)
            error_message = self.env['mtd.display_message'].consturct_error_message_to_display(
                url=url,
                code=response.status_code,
                response_token=response_token
            )
            _logger.info("json_command - other error found:- {error} ".format(error=error_message))
            record.response_from_hmrc = error_message
            if api_tracker:
                return werkzeug.utils.redirect(
                    "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=module_name) +
                    '&menu_id={menu}&action={action}'.format(menu=menu_id, action=action)
                )
            return True

    def process_successful_response(self, record=None, api_tracker=None):
        success_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(),
                                                        time=datetime.now().time())
                + "Congratulations ! The connection succeeded. \n"
                + "Please check the VAT logs. \n"
        )
        record.response_from_hmrc = success_message
        if api_tracker:
            _logger.info(
                "json_command - response received ok we have record id so we " +
                "return werkzeug.utils.redirect "
            )
            _logger.info(
                "-------Redirect is:- " +
                "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=api_tracker.module_name) +
                "menu_id={menu}&action={action}".format(menu=api_tracker.menu_id, action=api_tracker.action)
            )
            return werkzeug.utils.redirect(
                "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=api_tracker.module_name) +
                "menu_id={menu}&action={action}".format(menu=api_tracker.menu_id, action=api_tracker.action)
            )
        return True

    def add_liabilities_log(self, response):
        response_logs = json.loads(response.text)
        logs = response_logs['liabilities']
        for log in logs:
            liabilities_logs = self.env["mtd_vat.vat_liabilities_log"].search([
                ('from_date', '=', logs['from']),
                ('to_date', '=', logs["to"])
            ])
            if liabilities_logs:
                liabilities_logs.from_date = log['from']
                liabilities_logs.to_date = log['to']
                liabilities_logs.type = log["type"]
                liabilities_logs.due = log["due"]
                liabilities_logs.outstanding_amount = log["outstandingAmount"]
                liabilities_logs.original_amount = log["originalAmount"]
            else:
                liabilities_logs = liabilities_logs.create({
                    'from_date': log['from'],
                    'to_date': log['to'],
                    'type': log["type"],
                    'due': log["due"],
                    'outstanding_amount': log["outstandingAmount"],
                    'original_amount': log["originalAmount"]
                })

    def add_obligation_logs(self, response=None):
        response_logs = json.loads(response.text)
        logs = response_logs['obligations']
        for log in logs:
            received = ""
            if 'received' in log.keys():
                received = log['received']

            obligation_logs = self.env['mtd_vat.vat_obligations_logs'].search([
                ('start', '=', log['start']),
                ('end', '=', log['end'])
            ])
            if obligation_logs:
                obligation_logs.start = log['start']
                obligation_logs.end = end = log['end']
                obligation_logs.period_key = log['periodKey']
                obligation_logs.status = log['status']
                obligation_logs.received = received
                obligation_logs.due = due = log['due']
            else:
                obligation_logs = obligation_logs.create({
                    'start': log['start'],
                    'end': log['end'],
                    'period_key': log['periodKey'],
                    'status': log['status'],
                    'received': received,
                    'due': log['due']
                })

    def add_payments_logs(self, response=None, record=None):
        response_logs = json.loads(response.text)
        logs = response_logs['payments']
        payments_logs = self.env['mtd_vat.vat_obligations_logs']
        for log in logs:
            payments_logs = payments_logs.create({
                'start': record.from_date,
                'end': record.to_date,
                'amount': log["amount"],
                "received": log["received"]
            })
