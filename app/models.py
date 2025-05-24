from pydantic import BaseModel, EmailStr, constr, condecimal, conint
from typing import Optional, List, Literal
from datetime import datetime

class UsuarioBase(BaseModel):
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    senha: constr(min_length=6)  # senha com no mínimo 6 caracteres

class UsuarioDB(UsuarioBase):
    id: int
    senha_hash: str

    class Config:
        from_attributes = True

class ProdutoBase(BaseModel):
    nome: constr(min_length=1)
    preco: condecimal(gt=0, max_digits=10, decimal_places=2)
    unidade: constr(min_length=1)

class ProdutoCreate(ProdutoBase):
    ativo: bool = True  # Define ativo como True por padrão

class ProdutoDB(ProdutoBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class ItemPedidoBase(BaseModel):
    produto_id: conint(gt=0)
    quantidade: condecimal(gt=0)
    preco_unitario: condecimal(gt=0, max_digits=10, decimal_places=2)

class ItemPedidoDB(ItemPedidoBase):
    id: int
    pedido_id: int

class ItemPedidoCreate(ItemPedidoBase):
    pass



class PedidoBase(BaseModel):
    data: datetime
    status: Literal["Pendente", "Aprovado", "Cancelado", "Entregue"] = "Pendente"
    total: Optional[condecimal(ge=0, max_digits=12, decimal_places=2)] = None  # Total opcional, calculado no backend

class PedidoCreate(PedidoBase):
    usuario_id: conint(gt=0)  # Garante que usuario_id seja um inteiro positivo
    itens: List[ItemPedidoCreate]

class PedidoDB(PedidoBase):
    id: int
    usuario_id: int
    itens: List[ItemPedidoDB] = []

    class Config:
        from_attributes = True