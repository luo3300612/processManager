from sqlalchemy import Column, String, create_engine, Integer, Date, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta
from functools import singledispatch, reduce
from operator import add

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

    is_completed = Column(Boolean, default=False)  # 是否完成

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


def wrap_up(affair):
    """
    结束一个事务
    """
    affair.end_day = date.today()
    affair.is_completed = True
    session.commit()
    print(f"{affair.name} is completed")


def record(obj, workload, date=date.today(), thoughts=""):  # TODO 检查是否完成，完成自动warp
    """
    工作记录
    """
    affair = query_affair(obj)
    if not affair:
        print("Affair Not Found")
        return
    rec = session.query(Record).filter(Record.affair_id == affair.id).filter(Record.date == date.today()).first()
    if rec:
        rec.workload += workload
    else:
        rec = Record(workload=workload, thoughts=thoughts, date=date)
        rec.affair = affair

    affair.process_status += workload
    if affair.process_status >= affair.workload:
        affair.process_status = affair.workload
        wrap_up(affair)
    session.commit()


@singledispatch
def query_affair(obj):
    raise NotImplementedError


@query_affair.register(str)
def _(name):
    """
    根据姓名查询
    """
    affair = session.query(Affair).filter(Affair.name == name).first()
    if not affair:
        return False
    return affair


@query_affair.register(int)
def _(id):
    """
    根据id查询
    """
    affair = session.query(Affair).filter(Affair.id == id).first()
    if not affair:
        return False
    return affair


def query_record(affair):
    records = session.query(Record).filter(Record.affair_id == affair.id).all()
    return records


def query_all():
    """
    查询所有记录
    """
    affairs = session.query(Affair).all()
    if not affairs:
        return False
    return affairs


def display(affairs):
    """
    展示查询结果
    """
    for affair in affairs:
        try:
            div = (affair.process_status + affair.start_from) / affair.workload
            print(
                f"""[{affair.id}]<{affair.description.upper()}:{affair.name},process status:[{int(
                    div * 20) * '#'}{(20 - int(
                    div * 20)) * '-'}],{div * 100:.2f}%,{affair.process_status + affair.start_from}/{affair.workload}>""")
        except ZeroDivisionError as e:
            print(e)


def show_all():
    result = query_all()
    if result:
        display(result)
    else:
        print("Empty")


def show(obj):
    result = query_affair(obj)
    if result:
        display([result])
    else:
        print("Not Found")


def pred(affair):  # TODO refactor
    records = query_record(affair)
    if not records:
        print("No records")
        return
    num_of_work_day = len(records)
    total_workload = reduce(add, (rec.workload for rec in records))

    period = (date.today() - affair.start_day).days + 1
    if period == 0:
        period = 1

    average_workload_day = total_workload / period
    average_workload_workday = total_workload / num_of_work_day

    expect_workday_salty_fish = int((affair.workload - affair.process_status) / average_workload_day)
    expect_workday_work_everyday = int((affair.workload - affair.process_status) / average_workload_workday)

    today = date.today()
    expect_end_day_work_salty_fish = today + timedelta(days=expect_workday_salty_fish)
    expect_end_day_work_everyday = today + timedelta(days=expect_workday_work_everyday)

    return expect_end_day_work_salty_fish, expect_end_day_work_everyday


def monitor(obj):
    affair = query_affair(obj)
    if not affair:
        print("Not Found")
        return
    fish, dog = pred(affair)
    print(f"You will complete {affair.name} on:")
    print(fish.strftime("%Y-%m-%d"), "If you work like a salty fish")
    print(dog.strftime("%Y-%m-%d"), "If you work like a dog")


# TODO refactor 写单元测试！！！！

# display(query("C"))
# display(query_all())

# register("A", "asd", "hahah")
# register("A", "abc", "hehe")
# register("B", "h", "ca")
# register("C", 500, "ca")
#
# record("C", 30, "wtf")
#
# record("A", 5)
# wrap_up("B")


# register(name="计算机视觉——算法与应用", workload=565, description="book", start_from=205)
# register(name="学习OpenCV", workload=492, description="book", start_from=0)
# record(name="计算机视觉——算法与应用", workload=236 - 205)
# record(name="学习OpenCV", workload=25)
# record(name="计算机视觉——算法与应用", workload=261-236)
# record(name="学习OpenCV", workload=28-25)

#
#
#
if __name__ == '__main__':
    monitor(1)

# TODO 周统计
