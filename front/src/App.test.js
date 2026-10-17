import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { dictionaryAPI } from './api/services';

jest.mock('./api/services', () => ({
  dictionaryAPI: { getList: jest.fn() },
  studyAPI: {},
  authAPI: {},
}));

test('renders login for an unauthenticated learner', async () => {
  localStorage.clear();
  dictionaryAPI.getList.mockResolvedValue({ data: [] });
  render(<App />);
  await waitFor(() => expect(dictionaryAPI.getList).toHaveBeenCalled());
  expect(screen.getByRole('button', { name: /로그인/ })).toBeInTheDocument();
  expect(document.querySelector('input[type="password"]')).toBeInTheDocument();
});
