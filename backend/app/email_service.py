"""邮件发送服务：通过 SMTP 发送验证码邮件（用于邮箱注册）。

支持两种常见配置：
  - 465 端口 + SSL（QQ 邮箱 / 163 / 企业邮箱常用）
  - 587 端口 + STARTTLS
若未配置 SMTP，开发模式下会在日志中打印验证码并允许接口回显，便于本地联调。
"""
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from .config import settings


def is_smtp_configured() -> bool:
    """是否已完成 SMTP 配置。"""
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _sender_address() -> str:
    return settings.SMTP_FROM or settings.SMTP_USER


def _build_message(to: str, subject: str, html: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((str(Header(settings.SMTP_FROM_NAME, "utf-8")), _sender_address()))
    msg["To"] = to
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send_email(to: str, subject: str, html: str) -> None:
    """发送一封 HTML 邮件；失败会抛出异常，由调用方处理。"""
    if not is_smtp_configured():
        raise RuntimeError("SMTP 未配置")

    msg = _build_message(to, subject, html)
    sender = _sender_address()

    if settings.SMTP_USE_SSL:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=20) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(sender, [to], msg.as_string())
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(sender, [to], msg.as_string())


def verification_email_html(code: str, minutes: int) -> str:
    """验证码邮件正文（内联样式，兼容主流邮箱客户端）。"""
    return f"""\
<div style="margin:0;padding:24px;background:#f4f6fb;font-family:'Microsoft YaHei',Arial,sans-serif;">
  <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;
              box-shadow:0 8px 24px rgba(16,24,40,.08);">
    <div style="background:linear-gradient(122deg,#1677ff 0%,#3b9dff 48%,#22d3ee 100%);
                padding:28px 32px;color:#ffffff;">
      <div style="font-size:18px;font-weight:700;letter-spacing:.5px;">汽车养护预约服务系统</div>
      <div style="font-size:13px;opacity:.9;margin-top:6px;">邮箱注册验证码</div>
    </div>
    <div style="padding:32px;">
      <p style="margin:0 0 14px;color:#16202e;font-size:15px;">您好，您正在注册本系统账号，验证码为：</p>
      <div style="text-align:center;margin:22px 0;">
        <span style="display:inline-block;padding:14px 26px;border-radius:12px;background:#eaf2ff;
                     color:#1677ff;font-size:32px;font-weight:800;letter-spacing:8px;">{code}</span>
      </div>
      <p style="margin:0 0 8px;color:#5b6779;font-size:13.5px;line-height:1.7;">
        验证码 {minutes} 分钟内有效，请勿泄露给他人。<br />
        如果这不是您本人的操作，请忽略本邮件。
      </p>
      <div style="margin-top:22px;padding-top:16px;border-top:1px dashed #e6ebf3;
                  color:#909399;font-size:12px;line-height:1.7;">
        本邮件由系统自动发送，请勿直接回复。
      </div>
    </div>
  </div>
</div>"""
