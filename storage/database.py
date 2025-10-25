"""
데이터베이스 연결 및 세션 관리
SQLAlchemy 엔진 및 세션 생성
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from core.logger import get_logger
from storage.models import Base

logger = get_logger()


class Database:
    """데이터베이스 관리 클래스"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """데이터베이스 초기화"""
        if self._initialized:
            return
        
        # SQLite 사용 시 특별 설정
        if settings.database_url.startswith("sqlite"):
            # 데이터베이스 파일 경로 확인 및 생성
            db_path = settings.get_database_path()
            if db_path:
                db_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"SQLite database path: {db_path}")
            
            # SQLite 엔진 생성 (멀티스레드 지원)
            self.engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False  # SQL 쿼리 로깅 (디버그 시 True)
            )
            
            # WAL 모드 활성화 (동시성 향상)
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        else:
            # PostgreSQL 등 다른 데이터베이스
            self.engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,  # 연결 확인
                echo=False
            )
        
        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = True
        logger.info(f"Database engine initialized: {settings.database_url}")
    
    def create_tables(self):
        """모든 테이블 생성"""
        if not self._initialized:
            self.initialize()
        
        Base.metadata.create_all(bind=self.engine)
        logger.info("All database tables created")
    
    def drop_tables(self):
        """모든 테이블 삭제 (주의!)"""
        if not self._initialized:
            self.initialize()
        
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self) -> Session:
        """새 세션 반환"""
        if not self._initialized:
            self.initialize()
        
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        세션 컨텍스트 매니저
        자동 커밋/롤백 처리
        
        사용 예:
            with db.session_scope() as session:
                job = session.query(Job).first()
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


# 전역 데이터베이스 인스턴스
db = Database()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency용 데이터베이스 세션 제공
    
    사용 예:
        @app.get("/jobs")
        def get_jobs(db: Session = Depends(get_db)):
            return db.query(Job).all()
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def init_database():
    """데이터베이스 초기화 (애플리케이션 시작 시 호출)"""
    db.initialize()
    db.create_tables()
    logger.info("Database initialization completed")


if __name__ == "__main__":
    # 테스트
    from storage.models import Job, JobType
    
    print("🗄️  Database Test")
    print("=" * 60)
    
    # 데이터베이스 초기화
    init_database()
    
    # 테스트 데이터 삽입
    with db.session_scope() as session:
        # 기존 데이터 확인
        count = session.query(Job).count()
        print(f"Existing jobs: {count}")
        
        # 테스트 작업 추가
        if count == 0:
            test_job = Job(
                name="test_system_monitor",
                description="시스템 모니터링 테스트 작업",
                job_type=JobType.MONITORING,
                script_path="scripts/monitoring/system_monitor.py",
                cron_expression="*/5 * * * *",  # 5분마다
                enabled=True
            )
            session.add(test_job)
            session.commit()
            print("✅ Test job created")
        
        # 작업 조회
        jobs = session.query(Job).all()
        print(f"\n📋 Jobs in database:")
        for job in jobs:
            print(f"   - {job.name} ({job.job_type.value})")
            print(f"     Cron: {job.cron_expression}")
            print(f"     Enabled: {job.enabled}")
    
    print("\n✅ Database test completed")
    print(f"📂 Database location: {settings.get_database_path()}")
