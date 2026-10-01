-- EduLead uses Django ORM in the application. These are equivalent simple JOIN examples for viva/report.
-- 1. Leads with counsellor and office
SELECT l.id,l.student_name,l.status,l.source,u.first_name,u.last_name,o.name AS office
FROM crm_lead l LEFT JOIN crm_employeeprofile ep ON l.assigned_to_id=ep.id LEFT JOIN auth_user u ON ep.user_id=u.id LEFT JOIN crm_office o ON l.office_id=o.id;
-- 2. Source quality
SELECT source,COUNT(*) total,SUM(status='ENROLLED') admissions,ROUND(SUM(status='ENROLLED')*100/COUNT(*),1) conversion_rate FROM crm_lead GROUP BY source ORDER BY admissions DESC;
-- 3. Counsellor performance
SELECT u.username,COUNT(l.id) assigned,SUM(l.status='ENROLLED') converted FROM crm_employeeprofile ep JOIN auth_user u ON ep.user_id=u.id LEFT JOIN crm_lead l ON l.assigned_to_id=ep.id WHERE ep.role='COUNSELLOR' GROUP BY ep.id,u.username;
-- 4. Lead history
SELECT l.student_name,a.activity_type,a.note,a.created_at,u.username FROM crm_leadactivity a JOIN crm_lead l ON a.lead_id=l.id LEFT JOIN auth_user u ON a.user_id=u.id ORDER BY a.created_at DESC;
