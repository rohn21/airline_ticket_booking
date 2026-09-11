import io
import base64
import qrcode


class QRService:
    @staticmethod
    def generate_qr_bytes(data: str) -> bytes:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        return buffer.getvalue()


    @staticmethod
    def generate_qr_base64(data: str) -> str:
        qr_bytes = QRService.generate_qr_bytes(data)
        return base64.b64encode(qr_bytes).decode("utf-8")
