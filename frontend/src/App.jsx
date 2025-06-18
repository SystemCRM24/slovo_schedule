import './App.css';
import DateRangePicker from "./components/ui/DateRangePicker/index.jsx";
import React from "react";
import { Container } from "react-bootstrap";
import Schedule from "./components/Schedule/index.jsx";
import { WorkScheduleContextProvider } from "./contexts/WorkSchedule/provider.jsx";
import { ScheduleContextProvider } from "./contexts/Schedule/provider.jsx";
import { AppContextProvider } from "./contexts/App/provider.jsx";

function App() {
    return (
        <AppContextProvider>
            <Container fluid className={'mt-2'}>
                <DateRangePicker />
            </Container>
            <WorkScheduleContextProvider schedule={{}}>
                <ScheduleContextProvider schedule={{}}>
                    <Schedule  />
                </ScheduleContextProvider>
            </WorkScheduleContextProvider>
        </AppContextProvider>
    );
}

export default App;