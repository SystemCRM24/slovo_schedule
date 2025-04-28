import React from "react";
import {WorkScheduleContext, useCreateWorkScheduleContext} from "./context.js";

export function WorkScheduleContextProvider({children, schedule}) {
    const context = useCreateWorkScheduleContext(schedule);
    return <WorkScheduleContext.Provider value={context}>{children}</WorkScheduleContext.Provider>
}

export function useWorkScheduleContext() {
    const context = React.useContext(WorkScheduleContext);
    if (!context) throw new Error('Use services context within provider!');
    return context;
}
