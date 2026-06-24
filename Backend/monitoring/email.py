from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

class EmergencyEmailService:
    @staticmethod
    def send_critical_alert(email_target, device_name, heart_rate, oxygen_level, timestamp):
        if not email_target:
            return False

        subject = '🚨 هشدار پزشکی اضطراری (سیستم مانیتورینگ علائم حیاتی)'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Tahoma, Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; text-align: right; }}
                .container {{ max-width: 600px; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-top: 6px solid #d9534f; }}
                .header {{ background-color: #fcf8e3; padding: 20px; text-align: center; border-bottom: 1px solid #fbeed5; }}
                .header h2 {{ color: #b94a48; margin: 0; font-size: 22px; }}
                .content {{ padding: 30px; color: #333333; line-height: 1.8; }}
                .device-info {{ background: #f8f9fa; padding: 15px; border-right: 4px solid #5bc0de; margin-bottom: 20px; border-radius: 4px; }}
                .vital-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .vital-table th, .vital-table td {{ padding: 12px; border: 1px solid #eeeeee; text-align: center; }}
                .vital-table th {{ background-color: #f5f5f5; color: #555555; }}
                .critical {{ color: #d9534f; font-weight: bold; background-color: #fdf7f7; }}
                .normal {{ color: #5cb85c; }}
                .footer {{ background-color: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #777777; border-top: 1px solid #eeeeee; }}
            </style>
        </head>
        <body>
            <div class="container" style="margin: 0 auto;">
                <div class="header">
                    <h2>🚨 هشدار وضعیت بحرانی بیمار</h2>
                </div>
                <div class="content">
                    <p>با سلام،</p>
                    <p>سیستم پایش آنلاین علائم حیاتی یک وضعیت ناپایدار و بحرانی را برای دستگاه زیر گزارش کرده است:</p>
                    
                    <div class="device-info">
                        <strong>نام دستگاه سخت‌افزاری:</strong> {device_name}<br>
                        <strong>زمان ثبت رویداد:</strong> {timestamp}
                    </div>

                    <p>آخرین مقادیر دریافت شده از سنسور به شرح زیر است:</p>
                    
                    <table class="vital-table">
                        <thead>
                            <tr>
                                <th>نوع شاخص</th>
                                <th>مقدار ثبت شده</th>
                                <th>وضعیت</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>ضربان قلب (BPM)</td>
                                <td class="{"critical" if heart_rate > 120 or heart_rate < 50 else "normal"}">{heart_rate} BPM</td>
                                <td>{"❌ بحرانی" if heart_rate > 120 or heart_rate < 50 else "✅ نرمال"}</td>
                            </tr>
                            <tr>
                                <td>سطح اکسیژن خون (SpO2)</td>
                                <td class="{"critical" if oxygen_level < 92 else "normal"}">{oxygen_level}%</td>
                                <td>{"❌ بحرانی" if oxygen_level < 92 else "✅ نرمال"}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <p style="color: #b94a48; font-weight: bold; margin-top: 25px;">⚠️ اقدام فوری: لطفاً هرچه سریع‌تر وضعیت بیمار را بررسی نمایید.</p>
                </div>
                <div class="footer">
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
            print(f"[SUCCESS] Beautiful HTML Emergency email sent to {email_target}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send HTML email: {e}")
            return False