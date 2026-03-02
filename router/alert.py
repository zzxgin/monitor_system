from flask import request
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity
from lib.response import response
from model import AlertRule, AlertHistory, Server, User, AuditLog
from model import db
from lib.jwt_utils import admin_required

class AlertRuleAPI(Resource):
    @admin_required
    def get(self):
        try:
            server_id = request.args.get('server_id')
            if server_id:
                rules = AlertRule.query.filter_by(server_id=server_id).all()
            else:
                rules = AlertRule.query.all()
                
            result = []
            for rule in rules:
                rule_dict = {
                    'id': rule.id,
                    'server_id': rule.server_id,
                    'server_name': rule.server.server_name if rule.server else 'Unknown',
                    'metric_type': rule.metric_type,
                    'threshold': float(rule.threshold),
                    'silence_minutes': rule.silence_minutes,
                    'is_enabled': rule.is_enabled,
                    'created_at': str(rule.created_at)
                }
                result.append(rule_dict)
                
            return response(data=result, message="获取告警规则成功")
        except Exception as e:
            return response(message=f"获取告警规则失败: {str(e)}", code=500)

    @admin_required
    def post(self):
        try:
            data = request.json
            server_id = data.get('server_id')
            metric_type = data.get('metric_type')
            threshold = data.get('threshold')
            
            if not all([server_id, metric_type, threshold]):
                return response(message="缺少必要参数", code=400)
                
            # 检查是否已存在相同规则
            existing = AlertRule.query.filter_by(
                server_id=server_id, 
                metric_type=metric_type
            ).first()
            
            if existing:
                return response(message="该服务器已存在相同类型的监控规则", code=400)
                
            rule = AlertRule(
                server_id=server_id,
                metric_type=metric_type,
                threshold=threshold,
                silence_minutes=data.get('silence_minutes', 60),
                is_enabled=data.get('is_enabled', True)
            )
            db.session.add(rule)
            db.session.commit()
            
            # 审计日志
            current_user_id = get_jwt_identity()
            current_user = User.get_by_id(current_user_id) if current_user_id else None
            AuditLog.log(current_user, 'CREATE_ALERT_RULE', f'rule_id={rule.id}', details=str(data))
            
            return response(message="创建告警规则成功")
        except Exception as e:
            return response(message=f"创建告警规则失败: {str(e)}", code=500)

class AlertRuleDetailAPI(Resource):
    @admin_required
    def put(self, rule_id):
        try:
            rule = AlertRule.query.get(rule_id)
            if not rule:
                return response(message="规则不存在", code=404)
                
            data = request.json
            if 'threshold' in data:
                rule.threshold = data['threshold']
            if 'silence_minutes' in data:
                rule.silence_minutes = data['silence_minutes']
            if 'is_enabled' in data:
                rule.is_enabled = data['is_enabled']
                
            db.session.commit()
            
            # 审计日志
            current_user_id = get_jwt_identity()
            current_user = User.get_by_id(current_user_id) if current_user_id else None
            AuditLog.log(current_user, 'UPDATE_ALERT_RULE', f'rule_id={rule.id}', details=str(data))
            
            return response(message="更新告警规则成功")
        except Exception as e:
            return response(message=f"更新告警规则失败: {str(e)}", code=500)

    @admin_required
    def delete(self, rule_id):
        try:
            rule = AlertRule.query.get(rule_id)
            if not rule:
                return response(message="规则不存在", code=404)
                
            db.session.delete(rule)
            db.session.commit()
            
            # 审计日志
            current_user_id = get_jwt_identity()
            current_user = User.get_by_id(current_user_id) if current_user_id else None
            AuditLog.log(current_user, 'DELETE_ALERT_RULE', f'rule_id={rule_id}')
            
            return response(message="删除告警规则成功")
        except Exception as e:
            return response(message=f"删除告警规则失败: {str(e)}", code=500)

class AlertHistoryAPI(Resource):
    @admin_required
    def get(self):
        try:
            server_id = request.args.get('server_id')
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            query = AlertHistory.query.order_by(AlertHistory.triggered_at.desc())
            
            if server_id:
                query = query.filter_by(server_id=server_id)
                
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            result = []
            for item in pagination.items:
                item_dict = {
                    'id': item.id,
                    'server_id': item.server_id,
                    'server_name': item.server.server_name if item.server else 'Unknown',
                    'metric_type': item.metric_type,
                    'current_value': float(item.current_value),
                    'threshold_snapshot': float(item.threshold_snapshot) if item.threshold_snapshot else None,
                    'status': item.status,
                    'triggered_at': str(item.triggered_at),
                    'resolved_at': str(item.resolved_at) if item.resolved_at else None
                }
                result.append(item_dict)
                
            return response(data={
                'list': result,
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages
            }, message="获取告警历史成功")
        except Exception as e:
            return response(message=f"获取告警历史失败: {str(e)}", code=500)
