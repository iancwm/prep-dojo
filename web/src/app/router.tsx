import { Navigate, Route, Routes } from "react-router-dom";
import { LandingPage } from "../pages/LandingPage";
import { OperatorHomePage } from "../pages/OperatorHomePage";
import { OperatorSessionDetailPage } from "../pages/OperatorSessionDetailPage";
import { QuestionComposerPage } from "../pages/QuestionComposerPage";
import { ReviewPublishPage } from "../pages/ReviewPublishPage";
import ResultPage from "../pages/ResultPage";
import StudentSessionPage from "../pages/StudentSessionPage";

function SessionPreviewRedirect() {
  return <Navigate to="/operator" replace />;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/operator" element={<OperatorHomePage />} />
      <Route path="/operator/questions/new" element={<QuestionComposerPage />} />
      <Route path="/operator/questions/:questionId/review" element={<ReviewPublishPage />} />
      <Route path="/operator/sessions/:sessionId" element={<OperatorSessionDetailPage />} />
      <Route path="/operator/sessions/preview" element={<SessionPreviewRedirect />} />
      <Route path="/practice/:sessionId" element={<StudentSessionPage />} />
      <Route path="/practice/:sessionId/result" element={<ResultPage />} />
      <Route path="/student" element={<Navigate to="/practice/demo-session" replace />} />
      <Route path="/session" element={<Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
