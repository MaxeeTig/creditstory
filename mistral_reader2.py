 
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Optional
import os
from mistralai import Mistral
#from mistralai.models.chat_completion import ChatMessage
import json

class Loan(BaseModel):
    """
    Represents a loan/credit agreement with key financial details
    """
    bank_name: str = Field(
        ...,
        description="Full name of the bank or credit institution",
        example='АО "Райффайзенбанк"'
    )
    
    deal_date: date = Field(
        ...,
        description="Date when the loan agreement was signed (DD-MM-YYYY format)",
        example="18-05-2024"
    )
    
    deal_type: str = Field(
        ...,
        description="Type of the loan agreement",
        example="Договор займа (кредита)"
    )
    
    loan_type: str = Field(
        ...,
        description="Category of the loan",
        example="Иной заем (кредит)"
    )
    
    card_usage: bool = Field(
        ...,
        description="Whether a payment card is used for this loan",
        example=True
    )
    
    loan_amount: float = Field(
        ...,
        description="Principal amount of the loan",
        example=50000.00,
        gt=0
    )
    
    loan_currency: str = Field(
        ...,
        description="Currency of the loan (3-letter code)",
        example="RUB",
        min_length=3,
        max_length=3
    )
    
    termination_date: Optional[date] = Field(
        None,
        description="Date when the loan was terminated (DD-MM-YYYY format)",
        example="31-12-9999"
    )
    
    loan_status: Optional[str] = Field(
        ...,
        description="Current status of the loan",
        pattern="^(Active|Closed)$",
        example="Active"
    )

    @field_validator('deal_date', 'termination_date', mode='before')
    def parse_date(cls, value):
        if value is None:
            return None
        if isinstance(value, date):
            return value
        return datetime.strptime(value, "%d-%m-%Y").date()

api_key = os.environ.get("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY environment variable not set")

client = Mistral(api_key=api_key)

text = '''
1. АО "Райффайзенбанк": Иной заем (кредит)  Сведения об источнике   Основные сведения об обязательстве Кредитный отчет для субъекта ID запроса Пользователь Предоставлен 3280714d-29ab-406f-9b1a-ebdcc22aa333 9999ZZ999999 15-02-2025 15:07 Полное наименование ОГРН/ИНН Вид Акционерное общество "Райффайзенбанк" 1027739326449 7744000302Заимодавец (кредитор) – кредитная организация УИд договора: c463768a-168e-11ef-9106-cbf9777785a4-9 Дата обновления информации: 12-02-2025 Номер договора: CRD240518006021539088 Дата сделки Тип сделки Вид займа (кредита) Использование платежной картыСумма и валюта Дата прекращения по условиям сделки 18-05-2024 Договор займа (кредита) Иной заем (кредит) Да 50000,00 RUB 31-12-9999 Вид участия Солидарные должники Потреб. кредит(займ) Плавающая (переменная) проц. ставкаДата возникновения обязательстваДата расчета Заемщик 0 Да Нет 18-05-2024 11-02-2025 Цель займа (кредита) Погашение по графику платежейКредитная линия Цель не определена Да Кредитная линия с лимитом задолженности Денежное обязательство источникаДенежное обязательство субъектаСоглашение о новации Обяз-во получено в резул. перевода (перехода) долгаПрекращение обязательстваДата фактического прекращения Да Да Нет Нет Н/Д Н/Д Возникновение обязательства в результате получения части прав кредитора от другого лицаЧастичная передача прав кредитора другому лицуПартнерское финансированиеУИД сделки, по которой права кредитора частично переданы другому лицу Нет Нет Нет Н/Д Дата расчета ПСКmin ПСК % в год max ПСК % в год min ПСК в денежном выраженииmax ПСК в денежном выраженииmax ПСК % в год при снятии наличныхmax ПСК % в год при безналичном использовании При наличии вопросов обращайтесь в НБКИ: 8-495-221-78-37, 8-800-600-64-04 System version:
'''

try:
    # First get the raw response
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "system",
                "content": """Extract loan information as JSON with these exact field names: 
                bank_name, deal_date (DD-MM-YYYY), deal_type, loan_type, 
                card_usage (true/false), loan_amount (number), 
                loan_currency (3 letters), termination_date (DD-MM-YYYY or null).
                Format must be valid JSON. Example:
                {
                    "bank_name": "Bank Name",
                    "deal_date": "01-01-2023",
                    "deal_type": "Loan Type",
                    "loan_type": "Loan Category",
                    "card_usage": true,
                    "loan_amount": 10000,
                    "loan_currency": "RUB",
                    "termination_date": "31-12-2025"
                }"""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    # Try to parse the response
    json_str = response.choices[0].message.content
    
    # Clean the response if needed
    if json_str.startswith('[') and json_str.endswith(']'):
        json_str = json_str[1:-1]  # Remove brackets if it's a list
        
    loan_data = json.loads(json_str)
    
    # Convert to Loan object
    loan = Loan(**loan_data)
    
    # Determine status
    loan.loan_status = "Closed" if (loan.termination_date and 
                                  loan.termination_date.strftime("%d-%m-%Y") != "31-12-9999") else "Active"
    
    print("Successfully extracted loan information:")
    print(loan.model_dump_json(indent=2))
    
except json.JSONDecodeError:
    print("Failed to parse JSON response. Raw output:")
    print(json_str)
except Exception as e:
    print(f"Error occurred: {str(e)}")
    if 'json_str' in locals():
        print(f"Raw response: {json_str}")

