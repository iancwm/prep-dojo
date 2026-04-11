import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getAuthoredQuestion, submitAuthoredQuestionAttempt } from "../api/authored";
import { getPracticeSession, startPracticeSession } from "../api/practiceSessions";
import {
  buildStudentResult,
  buildStudentSession,
  createInitialDraft,
  loadStudentResult,
  mapBundleToStudentQuestion,
  saveStudentResult,
} from "../data/demoSession";
import type { AuthoredQuestionBundleRecord, StudentAttemptCreate } from "../types/api";
import type { StudentAnswerDraft, StudentResult, StudentSession } from "../types/student";
import { AnswerComposer } from "../components/student/AnswerComposer";
import { ProgressHeader } from "../components/student/ProgressHeader";
import { QuestionPrompt } from "../components/student/QuestionPrompt";
import { SessionCompleteCard } from "../components/student/SessionCompleteCard";
import { SessionIntroCard } from "../components/student/SessionIntroCard";
import { ErrorPanel } from "../components/shared/ErrorPanel";
import { LoadingBlock } from "../components/shared/LoadingBlock";
import "../styles/student.css";

interface StudentSessionPageViewProps {
  session: StudentSession;
  result: StudentResult | null;
  draft: StudentAnswerDraft;
  onStart: () => void;
  onSubmit: () => void;
  onChangeDraft: (value: StudentAnswerDraft) => void;
  onOpenResult: () => void;
  isStarting: boolean;
  isSubmitting: boolean;
}

export function StudentSessionPageView({
  session,
  result,
  draft,
  onStart,
  onSubmit,
  onChangeDraft,
  onOpenResult,
  isStarting,
  isSubmitting,
}: StudentSessionPageViewProps) {
  const question = session.questionQueue[0];
  const currentIndex = session.currentQuestionId ? 0 : session.attempts.length;

  return (
    <div className="page page--student">
      {session.status === "created" ? (
        <SessionIntroCard session={session} question={question} onStart={onStart} isStarting={isStarting} />
      ) : null}

      {session.status === "in_progress" ? (
        <div className="page-stack">
          <ProgressHeader
            sessionTitle={session.title}
            source={session.source}
            status={session.status}
            currentIndex={currentIndex}
            totalCount={session.questionQueue.length}
            remainingCount={Math.max(0, session.questionQueue.length - session.attempts.length)}
          />
          <QuestionPrompt question={question} />
          <AnswerComposer
            question={question}
            value={draft}
            onChange={onChangeDraft}
            onSubmit={onSubmit}
            isSubmitting={isSubmitting}
          />
        </div>
      ) : null}

      {session.status === "completed" && result ? (
        <SessionCompleteCard session={session} result={result} onViewResult={onOpenResult} />
      ) : null}
    </div>
  );
}

export default function StudentSessionPage() {
  const params = useParams();
  const navigate = useNavigate();
  const sessionId = params.sessionId ?? "";

  const [session, setSession] = useState<StudentSession | null>(null);
  const [bundle, setBundle] = useState<AuthoredQuestionBundleRecord | null>(null);
  const [result, setResult] = useState<StudentResult | null>(null);
  const [draft, setDraft] = useState<StudentAnswerDraft>({ responseType: "free_text" });
  const [loading, setLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setError("Missing session id.");
      setLoading(false);
      return;
    }

    let alive = true;

    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        const sessionRecord = await getPracticeSession(sessionId);
        const questionId = sessionRecord.current_question_id ?? sessionRecord.question_queue[0];
        if (!questionId) {
          throw new Error("This session does not have a queued question yet.");
        }

        const nextBundle = await getAuthoredQuestion(questionId);
        const question = mapBundleToStudentQuestion(nextBundle);
        const nextSession = buildStudentSession(sessionRecord, question);

        if (!alive) {
          return;
        }

        setBundle(nextBundle);
        setSession(nextSession);
        setDraft(createInitialDraft(question));
        setResult(loadStudentResult(sessionId));
      } catch (cause) {
        if (alive) {
          setError(cause instanceof Error ? cause.message : "Unable to load the practice session.");
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      alive = false;
    };
  }, [sessionId]);

  async function handleStart() {
    if (!sessionId || !bundle) {
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const sessionRecord = await startPracticeSession(sessionId);
      const question = mapBundleToStudentQuestion(bundle);
      setSession(buildStudentSession(sessionRecord, question));
      setDraft(createInitialDraft(question));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to start the session.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleSubmit() {
    if (!session || !bundle) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = buildAttemptPayload(bundle.question.id, session.sessionId, draft);
      const submitResult = await submitAuthoredQuestionAttempt(bundle.question.id, payload);
      const nextQuestion = mapBundleToStudentQuestion(bundle);
      const nextResult = buildStudentResult(session.sessionId, nextQuestion, draft, submitResult);
      const sessionRecord = await getPracticeSession(session.sessionId);
      const nextSession = buildStudentSession(sessionRecord, nextQuestion);

      saveStudentResult(nextResult);
      setResult(nextResult);
      setSession(nextSession);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to submit the answer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleOpenResult() {
    navigate(`/practice/${sessionId}/result`);
  }

  if (loading) {
    return (
      <div className="page page--student">
        <LoadingBlock label="Loading session" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page page--student">
        <ErrorPanel message={error} />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="page page--student">
        <ErrorPanel message="Session data is unavailable." />
      </div>
    );
  }

  return (
    <StudentSessionPageView
      session={session}
      result={result}
      draft={draft}
      onStart={handleStart}
      onSubmit={handleSubmit}
      onChangeDraft={setDraft}
      onOpenResult={handleOpenResult}
      isStarting={isStarting}
      isSubmitting={isSubmitting}
    />
  );
}

function buildAttemptPayload(
  questionId: string,
  sessionId: string,
  draft: StudentAnswerDraft,
): StudentAttemptCreate {
  if (draft.responseType === "multiple_choice") {
    return {
      question_id: questionId,
      session_id: sessionId,
      status: "submitted",
      response: {
        response_type: "multiple_choice",
        selected_option_id: draft.selectedOptionId ?? "",
      },
    };
  }

  if (draft.responseType === "oral_transcript") {
    return {
      question_id: questionId,
      session_id: sessionId,
      status: "submitted",
      response: {
        response_type: "oral_transcript",
        transcript: draft.transcript ?? "",
        duration_seconds: draft.durationSeconds ?? null,
      },
    };
  }

  return {
    question_id: questionId,
    session_id: sessionId,
    status: "submitted",
    response: {
      response_type: "free_text",
      content: draft.content ?? "",
    },
  };
}
