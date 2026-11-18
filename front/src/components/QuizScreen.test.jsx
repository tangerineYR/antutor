import { render, screen, fireEvent } from '@testing-library/react';
import QuizScreen from './QuizScreen';
import { quizAPI } from '../api/services';

jest.mock('../api/services', () => ({ quizAPI: { submitQuiz: jest.fn() } }));

const baseProps = {
    sessionId: '1', concept: 'inflation', userId: 'test-user',
    language: 'ko', onComplete: jest.fn(),
};

beforeEach(() => jest.clearAllMocks());

test.each([false, true])('shows empty content immediately (POST=%s)', (isPostTest) => {
    render(<QuizScreen {...baseProps} questions={[]} isPostTest={isPostTest} />);
    expect(screen.getByRole('heading', { name: '등록된 퀴즈가 없습니다' })).toBeInTheDocument();
    expect(screen.queryByText('퀴즈를 준비중입니다. 잠시만 기다려주세요.')).not.toBeInTheDocument();
    expect(quizAPI.submitQuiz).not.toHaveBeenCalled();
    expect(baseProps.onComplete).not.toHaveBeenCalled();
});

test.each([null, undefined])('changes loading (%s) into an empty result', (questions) => {
    const { rerender } = render(<QuizScreen {...baseProps} questions={questions} />);
    expect(screen.getByText('퀴즈를 준비중입니다. 잠시만 기다려주세요.')).toBeInTheDocument();
    rerender(<QuizScreen {...baseProps} questions={[]} />);
    expect(screen.getByRole('heading', { name: '등록된 퀴즈가 없습니다' })).toBeInTheDocument();
});

test('shows the English empty state', () => {
    render(<QuizScreen {...baseProps} language="en" questions={[]} />);
    expect(screen.getByRole('heading', {
        name: 'No quiz is available for this concept.',
    })).toBeInTheDocument();
});

test('displays an available question after loading completes', () => {
    const { rerender } = render(<QuizScreen {...baseProps} questions={null} isPostTest />);
    const questions = [{
        id: 1, concept: 'inflation', question: '인플레이션의 의미는 무엇인가요?',
        choices: ['선택지 1', '선택지 2', '선택지 3', '선택지 4', '선택지 5'],
    }];
    rerender(<QuizScreen {...baseProps} questions={questions} isPostTest />);
    expect(screen.queryByText('등록된 퀴즈가 없습니다')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /사후 테스트 시작하기/ }));
    expect(screen.getByRole('heading', { name: questions[0].question })).toBeInTheDocument();
    expect(screen.getByText('선택지 1')).toBeInTheDocument();
});
