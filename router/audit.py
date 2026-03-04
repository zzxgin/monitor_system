from flask import request
from flask_restful import Resource
from lib.response import response
from model import AuditLog
from lib.jwt_utils import admin_required

class AuditLogAPI(Resource):
    @admin_required
    def get(self):
        """
        获取审计日志列表（分页）
        查询参数:
        - page: 页码，默认1
        - per_page: 每页数量，默认20
        """
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            # 按时间倒序查询
            pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # 序列化结果
            logs = []
            for log in pagination.items:
                logs.append({
                    'id': log.id,
                    'user_id': log.user_id,
                    'username_snapshot': log.username_snapshot,
                    'action': log.action,
                    'target': log.target,
                    'details': log.details,
                    'client_ip': log.client_ip,
                    'created_at': str(log.created_at)
                })
                
            return response(data={
                'list': logs,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            })
            
        except Exception as e:
            return response(message=f"获取审计日志失败: {str(e)}", code=500)
