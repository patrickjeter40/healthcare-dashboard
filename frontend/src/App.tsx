import { LinearProgress } from "@mui/material";
import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";

const DashboardPage = lazy(() =>
  import("./pages/DashboardPage").then((module) => ({
    default: module.DashboardPage,
  })),
);
const NotFoundPage = lazy(() =>
  import("./pages/NotFoundPage").then((module) => ({
    default: module.NotFoundPage,
  })),
);
const PatientDetailPage = lazy(() =>
  import("./pages/PatientDetailPage").then((module) => ({
    default: module.PatientDetailPage,
  })),
);
const PatientsPage = lazy(() =>
  import("./pages/PatientsPage").then((module) => ({
    default: module.PatientsPage,
  })),
);
const CreatePatientPage = lazy(() =>
  import("./pages/PatientFormPages").then((module) => ({
    default: module.CreatePatientPage,
  })),
);
const EditPatientPage = lazy(() =>
  import("./pages/PatientFormPages").then((module) => ({
    default: module.EditPatientPage,
  })),
);

function App() {
  return (
    <Suspense fallback={<LinearProgress aria-label="Loading page" />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/patients/new" element={<CreatePatientPage />} />
          <Route path="/patients/:id/edit" element={<EditPatientPage />} />
          <Route path="/patients/:id" element={<PatientDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
