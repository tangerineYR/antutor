import api from './index';
import { quizAPI } from './services';

jest.mock('./index', () => ({
    get: jest.fn(),
    post: jest.fn(),
}));

beforeEach(() => jest.clearAllMocks());

test.each([
    ['opportunity cost', '/quiz/opportunity%20cost'],
    ['a?b#c', '/quiz/a%3Fb%23c'],
    ['인플레이션', '/quiz/%EC%9D%B8%ED%94%8C%EB%A0%88%EC%9D%B4%EC%85%98'],
])('encodes the quiz concept: %s', async (concept, url) => {
    const response = { data: [] };
    api.get.mockResolvedValue(response);
    await expect(quizAPI.getQuestions(concept)).resolves.toBe(response);
    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.get).toHaveBeenCalledWith(url);
});
