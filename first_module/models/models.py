# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class first_module(models.Model):
#     _name = 'first_module.first_module'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
#
# from odoo import models, fields, api
#
# class Course(models.Model):
#     _name = 'openacademy.course'
#
#     name = fields.Char(string="Title", required=True)
#     description = fields.Text()
#
# class Session(models.Model):
#     _name = 'openacademy.session'
#     name = fields.Char(required=True)
#     start_date = fields.Date()
#     duration = fields.Float(digits=(6, 2), help="Duration in days")
#     seats = fields.Integer(string="Number of seats")
