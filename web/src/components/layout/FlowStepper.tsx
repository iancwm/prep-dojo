type FlowStep = {
  title: string;
  detail: string;
};

type FlowStepperProps = {
  steps: readonly FlowStep[];
  activeStep?: number;
};

export function FlowStepper({ steps, activeStep = 0 }: FlowStepperProps) {
  return (
    <ol className="flow-stepper">
      {steps.map((step, index) => {
        const isActive = index === activeStep;
        const isComplete = index < activeStep;

        return (
          <li
            key={step.title}
            className={`flow-stepper__item${isActive ? " flow-stepper__item--active" : ""}${isComplete ? " flow-stepper__item--complete" : ""}`}
          >
            <span className="flow-stepper__index">{index + 1}</span>
            <div>
              <div className="flow-stepper__title">{step.title}</div>
              <div className="flow-stepper__detail">{step.detail}</div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
