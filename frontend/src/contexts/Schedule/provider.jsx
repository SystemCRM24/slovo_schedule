import React from "react";
import {ScheduleContext, useCreateScheduleContext} from "./context.js";

export function ScheduleContextProvider({children, schedule}) {
    const context = useCreateScheduleContext(schedule);
    return <ScheduleContext.Provider value={context}>{children}</ScheduleContext.Provider>
}

export function useScheduleContext() {
    const context = React.useContext(ScheduleContext);
    if (!context) throw new Error('Use context within provider!');
    return context;
}
