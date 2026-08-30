from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

class EmergencyEmailService:
    @staticmethod
    def send_critical_alert(email_target, device_name, heart_rate, oxygen_level, timestamp):
        if not email_target:
            return False

        subject = '🚨 هشدار پزشکی اضطراری (سیستم مانیتورینگ علائم حیاتی)'
        
        hr_is_critical = heart_rate > 120 or heart_rate < 50
        hr_style = "color: #d9534f; font-weight: bold; background-color: #fdf7f7; padding: 12px; border: 1px solid #eeeeee;" if hr_is_critical else "color: #5cb85c; padding: 12px; border: 1px solid #eeeeee;"
        hr_status = "❌ بحرانی" if hr_is_critical else "✅ نرمال"

        ox_is_critical = oxygen_level < 92
        ox_style = "color: #d9534f; font-weight: bold; background-color: #fdf7f7; padding: 12px; border: 1px solid #eeeeee;" if ox_is_critical else "color: #5cb85c; padding: 12px; border: 1px solid #eeeeee;"
        ox_status = "❌ بحرانی" if ox_is_critical else "✅ نرمال"

        html_content = f"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" lang="fa" dir="rtl">
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
            <title>Emergency Alert</title>
        </head>
        <body dir="rtl" style="font-family: Tahoma, Geneva, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; text-align: right; direction: rtl;">
            <div dir="rtl" style="max-width: 600px; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-top: 6px solid #d9534f; margin: 0 auto; text-align: right; direction: rtl;">
                
                <div style="background-color: #fcf8e3; padding: 20px; text-align: center; border-bottom: 1px solid #fbeed5;">
                    <h2 style="color: #b94a48; margin: 0; font-size: 22px; font-family: Tahoma, Geneva, sans-serif;">🚨 هشدار وضعیت بحرانی بیمار</h2>
                </div>
                
                <div dir="rtl" style="padding: 30px; color: #333333; line-height: 1.8; text-align: right; direction: rtl;">
                    <p dir="rtl" style="text-align: right; direction: rtl; margin: 0 0 10px 0;">با سلام،</p>
                    <p dir="rtl" style="text-align: right; direction: rtl; margin: 0 0 20px 0;">سیستم پایش آنلاین علائم حیاتی یک وضعیت ناپایدار و بحرانی را برای دستگاه زیر گزارش کرده است:</p>
                    
                    <div dir="rtl" style="background: #f8f9fa; padding: 15px; border-right: 4px solid #5bc0de; margin-bottom: 20px; border-radius: 4px; text-align: right; direction: rtl;">
                        <p dir="rtl" style="margin: 0 0 8px 0; text-align: right; direction: rtl;">
                            <strong style="font-family: Tahoma, Geneva, sans-serif;">نام دستگاه سخت‌افزاری:</strong> 
                            <span dir="ltr" style="direction: ltr; unicode-bidi: embed; font-weight: bold; margin-right: 5px;">{device_name}</span>
                        </p>
                        <p dir="rtl" style="margin: 0; text-align: right; direction: rtl;">
                            <strong style="font-family: Tahoma, Geneva, sans-serif;">زمان ثبت رویداد:</strong> 
                            <span dir="ltr" style="direction: ltr; unicode-bidi: embed; margin-right: 5px;">{timestamp}</span>
                        </p>
                    </div>

                    <p dir="rtl" style="text-align: right; direction: rtl; margin: 0 0 15px 0;">آخرین مقادیر دریافت شده از سنسور به شرح زیر است:</p>
                    
                    <table dir="rtl" style="width: 100%; border-collapse: collapse; margin-top: 15px; text-align: center; direction: rtl;">
                        <thead>
                            <tr style="background-color: #f5f5f5; color: #555555;">
                                <th style="padding: 12px; border: 1px solid #eeeeee; font-weight: bold; font-family: Tahoma, Geneva, sans-serif;">نوع شاخص</th>
                                <th style="padding: 12px; border: 1px solid #eeeeee; font-weight: bold; font-family: Tahoma, Geneva, sans-serif;">مقدار ثبت شده</th>
                                <th style="padding: 12px; border: 1px solid #eeeeee; font-weight: bold; font-family: Tahoma, Geneva, sans-serif;">وضعیت</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 12px; border: 1px solid #eeeeee; font-family: Tahoma, Geneva, sans-serif;">ضربان قلب (BPM)</td>
                                <td dir="ltr" style="{hr_style} direction: ltr;">{heart_rate} BPM</td>
                                <td style="padding: 12px; border: 1px solid #eeeeee; font-family: Tahoma, Geneva, sans-serif;">{hr_status}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px; border: 1px solid #eeeeee; font-family: Tahoma, Geneva, sans-serif;">سطح اکسیژن خون (SpO2)</td>
                                <td dir="ltr" style="{ox_style} direction: ltr;">{oxygen_level}%</td>
                                <td style="padding: 12px; border: 1px solid #eeeeee; font-family: Tahoma, Geneva, sans-serif;">{ox_status}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <p dir="rtl" style="color: #b94a48; font-weight: bold; margin-top: 25px; text-align: right; direction: rtl; font-family: Tahoma, Geneva, sans-serif;">
                        ⚠️ <span style="margin-right: 5px;">اقدام فوری:</span> لطفاً هرچه سریع‌تر وضعیت بیمار را بررسی نمایید.
                    </p>
                </div>
                
                <div dir="rtl" style="background-color: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #777777; border-top: 1px solid #eeeeee; direction: rtl;">
                    این یک ایمیل خودکار از سرور مرکزی پایش سلامت (HMS) است. لطفاً به آن پاسخ ندهید.
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = strip_tags(html_content)
        
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_target]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            print(f"[SUCCESS] Emergency HTML email sent to {email_target}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send HTML email: {e}")
            return False