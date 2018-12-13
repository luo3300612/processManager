from sqlalchemy import Column, String, create_engine, Integer, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import date

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://root:12345@localhost:3306/processManager')


class Affair(Base):
    __tablename__ = 'tb_affair'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True)  # 项目名

    workload = Column(Integer, nullable=False)  # 总工作量
    start_from = Column(Integer, default=0)  # 注册时工作量
    process_status = Column(Integer, default=0)  # 当前进度

    start_day = Column(Date, default=date.today())  # 开始日期
    end_day = Column(Date)  # 完成日期

    description = Column(String(100))  # 项目描述

    # 关系
    records = relationship("Record", backref="affair")


class Record(Base):
    __tablename__ = 'tb_record'

    id = Column(Integer, primary_key=True)
    affair_id = Column(Integer, ForeignKey("tb_affair.id"))
    workload = Column(Integer, nullable=False)  # 日工作量
    date = Column(Date, default=date.today())  # 日期
    thoughts = Column(String(100))  # 感想


Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()


def register(name, workload, description, start_from=0):  # TODO 类型检查
    """
    开始一个事务
    """
    affair = Affair(name=name, start_from=start_from, workload=workload, description=description)
    session.add(affair)
    try:
        session.commit()
    except IntegrityError as e:
        print(e)
        session.rollback()


def wrap_up(name):
    """
    结束一个事务
    """
    affair = session.query(Affair).filter(Affair.name == name).first()
    affair.end_day = date.today()
    session.commit()


def record(name, workload, thoughts=""):
    """
    工作记录
    """
    rec = Record(workload=workload, thoughts=thoughts)
    affair = session.query(Affair).filter(Affair.name == name).first()
    if not affair:
        return
    rec.affair = affair

    affair.process_status += workload
    session.commit()


def query(name):
    """
    根据姓名查询
    """
    affair = session.query(Affair).filter(Affair.name == name).first()
    if not affair:
        return "Not Found!"
    return [affair]


def query_all():
    """
    查询所有记录
    """
    affairs = session.query(Affair).all()
    if not affairs:
        return "Not Found!"
    return affairs


def display(affairs):
    """
    展示查询结果
    """
    for affair in affairs:
        try:
            div = affair.process_status / affair.workload
            print(
                f"""<Project:{affair.name},process status:[{int(
                    div * 20) * '#'}{(20 - int(
                    div * 20)) * '-'}],{div * 100:.2f}%,{affair.process_status}/{affair.workload}>""")
        except ZeroDivisionError as e:
            print(e)


display(query("C"))
display(query_all())

# register("A", "asd", "hahah")
# register("A", "abc", "hehe")
# register("B", "h", "ca")
# register("C", 500, "ca")
#
# record("C", 30, "wtf")
#
# record("A", 5)
# wrap_up("B")
